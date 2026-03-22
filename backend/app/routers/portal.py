"""
Router: Portal do Cliente — Entrevistas atribuídas a clientes externos.
"""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.roteiro import Condicao, Entrevista, Evidencia, Pergunta, Roteiro
from app.models.user import User
from app.routers.auth import require_cliente
from app.services.antivirus import AntivirusUnavailableError, scan_file_with_clamav
from app.services.condicional import list_missing_required
from app.services.storage import download_evidencia_bytes, upload_evidencia_bytes

router = APIRouter()
settings = get_settings()


# ===== Schemas =====


class CondicaoPortalResponse(BaseModel):
    id: uuid.UUID
    operador: str
    valor: dict
    acao: str
    alvo_id: uuid.UUID | None
    model_config = {"from_attributes": True}


class PerguntaPortalResponse(BaseModel):
    id: uuid.UUID
    ordem: int
    texto: str
    tipo: str
    obrigatoria: bool
    secao: str | None
    metadado_alvo: str | None
    opcoes: dict | None
    condicoes: list[CondicaoPortalResponse] = []
    model_config = {"from_attributes": True}


class EntrevistaClienteResponse(BaseModel):
    id: uuid.UUID
    roteiro_id: uuid.UUID
    roteiro_titulo: str = ""
    roteiro_area: str | None = None
    status: str
    respostas: dict
    motivo_devolucao: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    model_config = {"from_attributes": True}


class EntrevistaClienteDetalhe(EntrevistaClienteResponse):
    perguntas: list[PerguntaPortalResponse] = []


class EvidenciaPortalResponse(BaseModel):
    id: uuid.UUID
    entrevista_id: uuid.UUID
    pergunta_id: uuid.UUID | None
    nome_arquivo: str
    mime_type: str | None
    tamanho_bytes: int | None
    hash_sha256: str
    storage_path: str
    created_at: datetime
    model_config = {"from_attributes": True}


class RespostasUpdate(BaseModel):
    respostas: dict[str, object]


# ===== Helpers =====


async def _get_entrevista_do_cliente(
    entrevista_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Entrevista:
    """Busca entrevista garantindo que pertence ao cliente autenticado."""
    stmt = select(Entrevista).where(
        Entrevista.id == entrevista_id,
        Entrevista.cliente_id == current_user.id,
    )
    entrevista = (await db.execute(stmt)).scalar_one_or_none()
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")
    return entrevista


def _build_list_response(entrevista: Entrevista, roteiro: Roteiro) -> EntrevistaClienteResponse:
    return EntrevistaClienteResponse(
        id=entrevista.id,
        roteiro_id=entrevista.roteiro_id,
        roteiro_titulo=roteiro.titulo,
        roteiro_area=roteiro.area,
        status=entrevista.status,
        respostas=entrevista.respostas,
        motivo_devolucao=entrevista.motivo_devolucao,
        created_at=entrevista.created_at,
        completed_at=entrevista.completed_at,
    )


# ===== Endpoints =====


@router.get("/entrevistas", response_model=list[EntrevistaClienteResponse])
async def listar_minhas_entrevistas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Lista entrevistas atribuídas ao cliente autenticado."""
    stmt = (
        select(Entrevista)
        .where(Entrevista.cliente_id == current_user.id)
        .options(selectinload(Entrevista.roteiro))
        .order_by(Entrevista.created_at.desc())
    )
    entrevistas = (await db.execute(stmt)).scalars().all()

    items: list[EntrevistaClienteResponse] = []
    for e in entrevistas:
        items.append(_build_list_response(e, e.roteiro))
    return items


@router.get("/entrevistas/{entrevista_id}", response_model=EntrevistaClienteDetalhe)
async def obter_minha_entrevista(
    entrevista_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Detalhe da entrevista com perguntas do roteiro (read-only)."""
    stmt = (
        select(Entrevista)
        .where(Entrevista.id == entrevista_id, Entrevista.cliente_id == current_user.id)
        .options(
            selectinload(Entrevista.roteiro)
            .selectinload(Roteiro.perguntas)
            .selectinload(Pergunta.condicoes),
            selectinload(Entrevista.evidencias),
        )
    )
    entrevista = (await db.execute(stmt)).scalar_one_or_none()
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")

    roteiro = entrevista.roteiro
    perguntas_ordenadas = sorted(roteiro.perguntas, key=lambda p: p.ordem)

    return EntrevistaClienteDetalhe(
        id=entrevista.id,
        roteiro_id=entrevista.roteiro_id,
        roteiro_titulo=roteiro.titulo,
        roteiro_area=roteiro.area,
        status=entrevista.status,
        respostas=entrevista.respostas,
        motivo_devolucao=entrevista.motivo_devolucao,
        created_at=entrevista.created_at,
        completed_at=entrevista.completed_at,
        perguntas=perguntas_ordenadas,
    )


@router.patch("/entrevistas/{entrevista_id}", response_model=EntrevistaClienteResponse)
async def atualizar_respostas(
    entrevista_id: uuid.UUID,
    data: RespostasUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Atualizar respostas — só se em_andamento ou devolvida."""
    entrevista = await _get_entrevista_do_cliente(entrevista_id, current_user, db)

    if entrevista.status not in ("em_andamento", "devolvida"):
        raise HTTPException(status_code=403, detail="Entrevista não pode ser editada neste status")

    entrevista.respostas = data.respostas
    await db.flush()
    await db.refresh(entrevista, ["roteiro"])
    return _build_list_response(entrevista, entrevista.roteiro)


@router.post("/entrevistas/{entrevista_id}/submeter", response_model=EntrevistaClienteResponse)
async def submeter_entrevista(
    entrevista_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Transiciona entrevista para 'submetida' após validar obrigatórias."""
    entrevista = await _get_entrevista_do_cliente(entrevista_id, current_user, db)

    if entrevista.status not in ("em_andamento", "devolvida"):
        raise HTTPException(status_code=403, detail="Apenas entrevistas em andamento ou devolvidas podem ser submetidas")

    # Validar perguntas obrigatórias
    result = await db.execute(
        select(Roteiro)
        .where(Roteiro.id == entrevista.roteiro_id)
        .options(selectinload(Roteiro.perguntas).selectinload(Pergunta.condicoes))
    )
    roteiro = result.scalar_one_or_none()
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    perguntas_ordenadas = sorted(roteiro.perguntas, key=lambda p: p.ordem)
    pendencias = list_missing_required(perguntas_ordenadas, entrevista.respostas)
    if pendencias:
        raise HTTPException(status_code=422, detail=f"Perguntas obrigatórias pendentes: {', '.join(pendencias)}")

    entrevista.status = "submetida"
    entrevista.motivo_devolucao = None  # limpa motivo anterior se existia
    await db.flush()
    await db.refresh(entrevista, ["roteiro"])
    return _build_list_response(entrevista, entrevista.roteiro)


# ===== Evidências =====


@router.get(
    "/entrevistas/{entrevista_id}/evidencias",
    response_model=list[EvidenciaPortalResponse],
)
async def listar_minhas_evidencias(
    entrevista_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Listar evidências da entrevista do cliente."""
    entrevista = await _get_entrevista_do_cliente(entrevista_id, current_user, db)

    result = await db.execute(
        select(Evidencia)
        .where(Evidencia.entrevista_id == entrevista.id)
        .order_by(Evidencia.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/entrevistas/{entrevista_id}/evidencias",
    response_model=EvidenciaPortalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_minha_evidencia(
    entrevista_id: uuid.UUID,
    file: UploadFile = File(...),
    pergunta_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Upload de evidência — só se em_andamento ou devolvida."""
    entrevista = await _get_entrevista_do_cliente(entrevista_id, current_user, db)

    if entrevista.status not in ("em_andamento", "devolvida"):
        raise HTTPException(status_code=403, detail="Upload não permitido neste status")

    if pergunta_id is not None:
        pergunta = await db.get(Pergunta, pergunta_id)
        if not pergunta or pergunta.roteiro_id != entrevista.roteiro_id:
            raise HTTPException(status_code=400, detail="Pergunta inválida para esta entrevista")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo inválido")

    payload = await file.read()
    if len(payload) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    limite_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(payload) > limite_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede limite de {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    if settings.CLAMAV_ENABLED:
        try:
            arquivo_limpo, assinatura = scan_file_with_clamav(payload)
        except AntivirusUnavailableError as exc:
            if not settings.CLAMAV_FAIL_OPEN:
                raise HTTPException(status_code=503, detail="Antivírus indisponível") from exc
            arquivo_limpo = True
            assinatura = None

        if not arquivo_limpo:
            detalhe = assinatura or "Ameaça detectada"
            raise HTTPException(status_code=400, detail=f"Arquivo reprovado pelo antivírus: {detalhe}")

    hash_sha256 = hashlib.sha256(payload).hexdigest()
    safe_filename = Path(file.filename).name or "anexo.bin"
    storage_key = (
        f"entrevistas/{entrevista.id}/"
        f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}-{safe_filename}"
    )

    try:
        storage_path = upload_evidencia_bytes(payload, storage_key, file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Falha ao armazenar evidência") from exc

    evidencia = Evidencia(
        entrevista_id=entrevista.id,
        pergunta_id=pergunta_id,
        nome_arquivo=safe_filename,
        mime_type=file.content_type,
        tamanho_bytes=len(payload),
        hash_sha256=hash_sha256,
        storage_path=storage_path,
        created_at=datetime.now(UTC),
    )

    db.add(evidencia)
    await db.flush()
    await db.refresh(evidencia)
    return evidencia


@router.delete(
    "/entrevistas/{entrevista_id}/evidencias/{evidencia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def excluir_minha_evidencia(
    entrevista_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Excluir evidência — só se em_andamento ou devolvida."""
    entrevista = await _get_entrevista_do_cliente(entrevista_id, current_user, db)

    if entrevista.status not in ("em_andamento", "devolvida"):
        raise HTTPException(status_code=403, detail="Exclusão não permitida neste status")

    evidencia = await db.get(Evidencia, evidencia_id)
    if not evidencia or evidencia.entrevista_id != entrevista.id:
        raise HTTPException(status_code=404, detail="Evidência não encontrada")

    await db.delete(evidencia)
    await db.flush()
    return None


@router.get("/entrevistas/{entrevista_id}/evidencias/{evidencia_id}/download")
async def baixar_minha_evidencia(
    entrevista_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cliente),
):
    """Download de evidência da entrevista do cliente."""
    entrevista = await _get_entrevista_do_cliente(entrevista_id, current_user, db)

    evidencia = await db.get(Evidencia, evidencia_id)
    if not evidencia or evidencia.entrevista_id != entrevista.id:
        raise HTTPException(status_code=404, detail="Evidência não encontrada")

    try:
        payload = download_evidencia_bytes(evidencia.storage_path)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Falha ao recuperar evidência") from exc

    return Response(
        content=payload,
        media_type=evidencia.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{evidencia.nome_arquivo}"',
            "Cache-Control": "no-store",
        },
    )
