"""
Router EP1: Roteiros de Entrevista — CRUD, Versionamento, Execução.
"""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.roteiro import Roteiro, Pergunta, Condicao, Entrevista, Evidencia
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.assistente_entrevista import suggest_retention_preview
from app.services.antivirus import AntivirusUnavailableError, scan_file_with_clamav
from app.services.condicional import compute_question_state, list_missing_required
from app.services.mapeamento import suggest_document_class
from app.services.storage import download_evidencia_bytes, upload_evidencia_bytes

router = APIRouter()
settings = get_settings()


# ===== Schemas =====

class CondicaoCreate(BaseModel):
    operador: str  # AND, OR, NOT, EQ, NEQ, GT, LT
    valor: dict
    acao: str  # mostrar, ocultar, pular_para, obrigar
    alvo_id: uuid.UUID | None = None


class PerguntaCreate(BaseModel):
    ordem: int
    texto: str
    tipo: str  # texto, numero, select, multi_select, boolean
    obrigatoria: bool = True
    secao: str | None = None
    metadado_alvo: str | None = None
    opcoes: dict | None = None
    condicoes: list[CondicaoCreate] = []


class PerguntaUpdate(BaseModel):
    ordem: int | None = None
    texto: str | None = None
    tipo: str | None = None
    obrigatoria: bool | None = None
    secao: str | None = None
    metadado_alvo: str | None = None
    opcoes: dict | None = None
    condicoes: list[CondicaoCreate] | None = None


class RoteiroCreate(BaseModel):
    titulo: str
    descricao: str | None = None
    area: str | None = None
    perguntas: list[PerguntaCreate] = []


class RoteiroUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    area: str | None = None
    status: str | None = None


class NovaVersaoRequest(BaseModel):
    motivo_versao: str


class CondicaoResponse(BaseModel):
    id: uuid.UUID
    operador: str
    valor: dict
    acao: str
    alvo_id: uuid.UUID | None
    model_config = {"from_attributes": True}


class PerguntaResponse(BaseModel):
    id: uuid.UUID
    ordem: int
    texto: str
    tipo: str
    obrigatoria: bool
    secao: str | None
    metadado_alvo: str | None
    opcoes: dict | None
    condicoes: list[CondicaoResponse] = []
    model_config = {"from_attributes": True}


class RoteiroResponse(BaseModel):
    id: uuid.UUID
    titulo: str
    descricao: str | None
    area: str | None
    versao: int
    status: str
    versao_pai_id: uuid.UUID | None
    motivo_versao: str | None
    criado_por: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    perguntas: list[PerguntaResponse] = []
    model_config = {"from_attributes": True}


class RoteiroListResponse(BaseModel):
    id: uuid.UUID
    titulo: str
    area: str | None
    versao: int
    status: str
    total_perguntas: int = 0
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    items: list[RoteiroListResponse]
    total: int
    page: int
    per_page: int


class SimulacaoRequest(BaseModel):
    respostas: dict[str, object] = {}


class PerguntaSimuladaResponse(BaseModel):
    id: uuid.UUID
    ordem: int
    texto: str
    tipo: str
    secao: str | None
    visivel: bool
    obrigatoria: bool


class SimulacaoResponse(BaseModel):
    perguntas: list[PerguntaSimuladaResponse]
    pendencias: list[str]
    pode_concluir: bool


class AssistentePreviewResponse(BaseModel):
    progresso_percentual: float
    respostas_preenchidas: int
    total_perguntas_ativas: int
    resumo: str
    pendencias: list[str]
    pcd_sugerido: str
    pcd_justificativa: str
    ttd_sugerida: str
    ttd_justificativa: str


class EntrevistaCreateRequest(BaseModel):
    respostas: dict[str, object] = {}
    cliente_id: uuid.UUID | None = None


class EntrevistaUpdateRequest(BaseModel):
    respostas: dict[str, object] | None = None
    status: str | None = None
    cliente_id: uuid.UUID | None = None
    motivo_devolucao: str | None = None


# Transições válidas: (status_atual, status_novo) -> set de roles que podem executar
_INTERNAL = {"admin", "gestor", "arquivista", "classificador", "auditor", "viewer"}
_CLIENT = {"cliente"}
_STATUS_TRANSITIONS: dict[tuple[str, str], set[str]] = {
    ("em_andamento", "submetida"): _CLIENT,
    ("em_andamento", "concluida"): _INTERNAL,
    ("em_andamento", "cancelada"): _INTERNAL,
    ("submetida", "concluida"): _INTERNAL,
    ("submetida", "devolvida"): _INTERNAL,
    ("submetida", "cancelada"): _INTERNAL,
    ("devolvida", "em_andamento"): _CLIENT,
    ("devolvida", "submetida"): _CLIENT,
}


class EntrevistaResponse(BaseModel):
    id: uuid.UUID
    roteiro_id: uuid.UUID
    entrevistador_id: uuid.UUID | None
    cliente_id: uuid.UUID | None = None
    status: str
    respostas: dict[str, object]
    motivo_devolucao: str | None = None
    created_at: datetime
    completed_at: datetime | None
    model_config = {"from_attributes": True}


class EvidenciaResponse(BaseModel):
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


class SugestaoClasseRequest(BaseModel):
    respostas: dict[str, object] | None = None


class SugestaoClasseResponse(BaseModel):
    entrevista_id: uuid.UUID
    sugestao_classe: str
    sugestao_justificativa: str


class EntrevistasResumoResponse(BaseModel):
    total: int
    por_status: dict[str, int]
    esta_semana: int
    este_mes: int


# ===== Endpoints =====

@router.get("", response_model=PaginatedResponse)
async def listar_roteiros(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    area: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    busca: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar roteiros com filtros e paginação."""
    query = select(Roteiro)

    if area:
        query = query.where(Roteiro.area == area)
    if status_filter:
        query = query.where(Roteiro.status == status_filter)
    if busca:
        query = query.where(Roteiro.titulo.ilike(f"%{busca}%"))

    # Total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginar
    query = query.offset((page - 1) * per_page).limit(per_page).order_by(Roteiro.updated_at.desc())
    result = await db.execute(query.options(selectinload(Roteiro.perguntas)))
    roteiros = result.scalars().all()

    items = []
    for r in roteiros:
        item = RoteiroListResponse(
            id=r.id,
            titulo=r.titulo,
            area=r.area,
            versao=r.versao,
            status=r.status,
            total_perguntas=len(r.perguntas),
            created_at=r.created_at,
        )
        items.append(item)

    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=RoteiroResponse, status_code=status.HTTP_201_CREATED)
async def criar_roteiro(
    data: RoteiroCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar novo roteiro de entrevista (US-001)."""
    roteiro = Roteiro(
        titulo=data.titulo,
        descricao=data.descricao,
        area=data.area,
        criado_por=current_user.id,
    )

    for p_data in data.perguntas:
        pergunta = Pergunta(
            ordem=p_data.ordem,
            texto=p_data.texto,
            tipo=p_data.tipo,
            obrigatoria=p_data.obrigatoria,
            secao=p_data.secao,
            metadado_alvo=p_data.metadado_alvo,
            opcoes=p_data.opcoes,
        )
        for c_data in p_data.condicoes:
            condicao = Condicao(
                operador=c_data.operador,
                valor=c_data.valor,
                acao=c_data.acao,
                alvo_id=c_data.alvo_id,
            )
            pergunta.condicoes.append(condicao)
        roteiro.perguntas.append(pergunta)

    db.add(roteiro)
    await db.flush()
    await db.refresh(roteiro, ["perguntas"])
    return roteiro


@router.get("/{roteiro_id}", response_model=RoteiroResponse)
async def obter_roteiro(
    roteiro_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter roteiro por ID com perguntas e condições."""
    result = await db.execute(
        select(Roteiro)
        .where(Roteiro.id == roteiro_id)
        .options(selectinload(Roteiro.perguntas).selectinload(Pergunta.condicoes))
    )
    roteiro = result.scalar_one_or_none()
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")
    return roteiro


@router.post("/{roteiro_id}/perguntas", response_model=PerguntaResponse, status_code=status.HTTP_201_CREATED)
async def adicionar_pergunta(
    roteiro_id: uuid.UUID,
    data: PerguntaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Adicionar pergunta com condições em um roteiro existente (US-001/US-002)."""
    roteiro = await db.get(Roteiro, roteiro_id)
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")
    if roteiro.status == "arquivado":
        raise HTTPException(status_code=400, detail="Roteiro arquivado não pode receber novas perguntas")

    pergunta = Pergunta(
        roteiro_id=roteiro_id,
        ordem=data.ordem,
        texto=data.texto,
        tipo=data.tipo,
        obrigatoria=data.obrigatoria,
        secao=data.secao,
        metadado_alvo=data.metadado_alvo,
        opcoes=data.opcoes,
    )
    for c_data in data.condicoes:
        pergunta.condicoes.append(
            Condicao(
                operador=c_data.operador,
                valor=c_data.valor,
                acao=c_data.acao,
                alvo_id=c_data.alvo_id,
            )
        )

    db.add(pergunta)
    await db.flush()
    await db.refresh(pergunta, ["condicoes"])
    return pergunta


@router.patch("/{roteiro_id}/perguntas/{pergunta_id}", response_model=PerguntaResponse)
async def atualizar_pergunta(
    roteiro_id: uuid.UUID,
    pergunta_id: uuid.UUID,
    data: PerguntaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar pergunta existente de um roteiro."""
    pergunta = await db.get(Pergunta, pergunta_id)
    if not pergunta or pergunta.roteiro_id != roteiro_id:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")

    roteiro = await db.get(Roteiro, roteiro_id)
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")
    if roteiro.status == "arquivado":
        raise HTTPException(status_code=400, detail="Roteiro arquivado não pode ser editado")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nenhuma alteração enviada")

    condicoes_payload = changes.pop("condicoes", None)
    for field, value in changes.items():
        setattr(pergunta, field, value)

    if condicoes_payload is not None:
        pergunta.condicoes.clear()
        for item in condicoes_payload:
            pergunta.condicoes.append(
                Condicao(
                    operador=item.operador,
                    valor=item.valor,
                    acao=item.acao,
                    alvo_id=item.alvo_id,
                )
            )

    await db.flush()
    await db.refresh(pergunta, ["condicoes"])
    return pergunta


@router.delete("/{roteiro_id}/perguntas/{pergunta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_pergunta(
    roteiro_id: uuid.UUID,
    pergunta_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir pergunta de roteiro, bloqueando se houver entrevista em andamento."""
    pergunta = await db.get(Pergunta, pergunta_id)
    if not pergunta or pergunta.roteiro_id != roteiro_id:
        raise HTTPException(status_code=404, detail="Pergunta não encontrada")

    entrevistas_ativas = (
        await db.execute(
            select(Entrevista).where(
                Entrevista.roteiro_id == roteiro_id,
                Entrevista.status == "em_andamento",
            )
        )
    ).scalars().all()
    if entrevistas_ativas:
        raise HTTPException(status_code=400, detail="Não é possível excluir pergunta com entrevista em andamento")

    await db.delete(pergunta)
    await db.flush()
    return None


@router.patch("/{roteiro_id}", response_model=RoteiroResponse)
async def atualizar_roteiro(
    roteiro_id: uuid.UUID,
    data: RoteiroUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar roteiro existente."""
    result = await db.execute(select(Roteiro).where(Roteiro.id == roteiro_id))
    roteiro = result.scalar_one_or_none()
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")
    if roteiro.status == "arquivado":
        raise HTTPException(status_code=400, detail="Roteiro arquivado não pode ser editado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(roteiro, field, value)

    await db.flush()
    await db.refresh(roteiro)
    return roteiro


@router.delete("/{roteiro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_roteiro(
    roteiro_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletar roteiro (soft delete via status=arquivado)."""
    result = await db.execute(select(Roteiro).where(Roteiro.id == roteiro_id))
    roteiro = result.scalar_one_or_none()
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    roteiro.status = "arquivado"
    await db.flush()


@router.post("/{roteiro_id}/versao", response_model=RoteiroResponse, status_code=status.HTTP_201_CREATED)
async def criar_nova_versao(
    roteiro_id: uuid.UUID,
    data: NovaVersaoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar nova versão de um roteiro (US-001 — Versionamento)."""
    result = await db.execute(
        select(Roteiro)
        .where(Roteiro.id == roteiro_id)
        .options(selectinload(Roteiro.perguntas).selectinload(Pergunta.condicoes))
    )
    original = result.scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    # Arquivar versão anterior
    original.status = "arquivado"

    # Criar nova versão
    nova = Roteiro(
        titulo=original.titulo,
        descricao=original.descricao,
        area=original.area,
        versao=original.versao + 1,
        versao_pai_id=original.id,
        motivo_versao=data.motivo_versao,
        criado_por=current_user.id,
    )

    # Copiar perguntas e condições
    for p in original.perguntas:
        nova_pergunta = Pergunta(
            ordem=p.ordem,
            texto=p.texto,
            tipo=p.tipo,
            obrigatoria=p.obrigatoria,
            secao=p.secao,
            metadado_alvo=p.metadado_alvo,
            opcoes=p.opcoes,
        )
        for c in p.condicoes:
            nova_condicao = Condicao(
                operador=c.operador,
                valor=c.valor,
                acao=c.acao,
                alvo_id=c.alvo_id,
            )
            nova_pergunta.condicoes.append(nova_condicao)
        nova.perguntas.append(nova_pergunta)

    db.add(nova)
    await db.flush()
    await db.refresh(nova, ["perguntas"])
    return nova


@router.post("/{roteiro_id}/simular", response_model=SimulacaoResponse)
async def simular_roteiro(
    roteiro_id: uuid.UUID,
    data: SimulacaoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executar dry-run de condições para um roteiro (US-002)."""
    result = await db.execute(
        select(Roteiro)
        .where(Roteiro.id == roteiro_id)
        .options(selectinload(Roteiro.perguntas).selectinload(Pergunta.condicoes))
    )
    roteiro = result.scalar_one_or_none()
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    perguntas_ordenadas = sorted(roteiro.perguntas, key=lambda question: question.ordem)
    perguntas_simuladas: list[PerguntaSimuladaResponse] = []
    for pergunta in perguntas_ordenadas:
        visivel, obrigatoria = compute_question_state(pergunta, data.respostas)
        perguntas_simuladas.append(
            PerguntaSimuladaResponse(
                id=pergunta.id,
                ordem=pergunta.ordem,
                texto=pergunta.texto,
                tipo=pergunta.tipo,
                secao=pergunta.secao,
                visivel=visivel,
                obrigatoria=obrigatoria,
            )
        )

    pendencias = list_missing_required(perguntas_ordenadas, data.respostas)
    return SimulacaoResponse(
        perguntas=perguntas_simuladas,
        pendencias=pendencias,
        pode_concluir=len(pendencias) == 0,
    )


@router.post("/{roteiro_id}/assistente-preview", response_model=AssistentePreviewResponse)
async def gerar_preview_assistido(
    roteiro_id: uuid.UUID,
    data: SimulacaoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gerar prévia assistida com progresso, sugestão PCD/TTD e pendências (US-090)."""
    result = await db.execute(
        select(Roteiro)
        .where(Roteiro.id == roteiro_id)
        .options(selectinload(Roteiro.perguntas).selectinload(Pergunta.condicoes))
    )
    roteiro = result.scalar_one_or_none()
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    perguntas_ordenadas = sorted(roteiro.perguntas, key=lambda question: question.ordem)
    perguntas_ativas = []
    for pergunta in perguntas_ordenadas:
        visivel, _obrigatoria = compute_question_state(pergunta, data.respostas)
        if visivel:
            perguntas_ativas.append(pergunta)

    respondidas = 0
    for pergunta in perguntas_ativas:
        valor = data.respostas.get(str(pergunta.id))
        if valor is None:
            continue
        if isinstance(valor, str) and valor.strip() == "":
            continue
        respondidas += 1

    total_ativas = len(perguntas_ativas)
    progresso = round((respondidas / total_ativas) * 100, 2) if total_ativas else 0.0
    pendencias = list_missing_required(perguntas_ordenadas, data.respostas)
    pcd_sugerido, pcd_justificativa = suggest_document_class(
        respostas=data.respostas,
        roteiro_titulo=roteiro.titulo,
        roteiro_area=roteiro.area,
    )
    ttd_sugerida, ttd_justificativa = suggest_retention_preview(data.respostas, pcd_sugerido)

    return AssistentePreviewResponse(
        progresso_percentual=progresso,
        respostas_preenchidas=respondidas,
        total_perguntas_ativas=total_ativas,
        resumo=(
            f"{respondidas}/{total_ativas} perguntas ativas respondidas; "
            f"{len(pendencias)} pendência(s) crítica(s) restante(s)."
        ),
        pendencias=pendencias,
        pcd_sugerido=pcd_sugerido,
        pcd_justificativa=pcd_justificativa,
        ttd_sugerida=ttd_sugerida,
        ttd_justificativa=ttd_justificativa,
    )


@router.post("/{roteiro_id}/entrevistas", response_model=EntrevistaResponse, status_code=status.HTTP_201_CREATED)
async def iniciar_entrevista(
    roteiro_id: uuid.UUID,
    data: EntrevistaCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Iniciar sessão de entrevista para anexos/evidências (US-003)."""
    roteiro = await db.get(Roteiro, roteiro_id)
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    cliente_id = data.cliente_id
    if cliente_id is not None:
        cliente = await db.get(User, cliente_id)
        if not cliente or cliente.role != "cliente":
            raise HTTPException(status_code=422, detail="Usuário informado não possui role cliente")
        if not cliente.is_active:
            raise HTTPException(status_code=422, detail="Usuário cliente está inativo")

    entrevista = Entrevista(
        roteiro_id=roteiro_id,
        entrevistador_id=current_user.id,
        cliente_id=cliente_id,
        status="em_andamento",
        respostas=data.respostas,
        created_at=datetime.now(UTC),
    )
    db.add(entrevista)
    await db.flush()
    await db.refresh(entrevista)
    return entrevista


@router.get("/{roteiro_id}/entrevistas", response_model=list[EntrevistaResponse])
async def listar_entrevistas_roteiro(
    roteiro_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar entrevistas de um roteiro."""
    roteiro = await db.get(Roteiro, roteiro_id)
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    result = await db.execute(
        select(Entrevista)
        .where(Entrevista.roteiro_id == roteiro_id)
        .order_by(Entrevista.created_at.desc())
    )
    return result.scalars().all()


@router.get("/entrevistas/resumo", response_model=EntrevistasResumoResponse)
async def resumo_entrevistas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resumo agregado de todas as entrevistas: total, por status, última semana e último mês."""
    from datetime import timedelta

    agora = datetime.now(UTC)
    inicio_semana = agora - timedelta(days=7)
    inicio_mes = agora - timedelta(days=30)

    todos_status = ["em_andamento", "submetida", "devolvida", "concluida", "cancelada"]

    # contagem total
    total_result = await db.execute(select(func.count()).select_from(Entrevista))
    total = total_result.scalar() or 0

    # contagem por status
    por_status: dict[str, int] = {}
    for st in todos_status:
        r = await db.execute(
            select(func.count()).select_from(Entrevista).where(Entrevista.status == st)
        )
        por_status[st] = r.scalar() or 0

    # criadas na última semana
    r_semana = await db.execute(
        select(func.count()).select_from(Entrevista).where(Entrevista.created_at >= inicio_semana)
    )
    esta_semana = r_semana.scalar() or 0

    # criadas no último mês
    r_mes = await db.execute(
        select(func.count()).select_from(Entrevista).where(Entrevista.created_at >= inicio_mes)
    )
    este_mes = r_mes.scalar() or 0

    return EntrevistasResumoResponse(
        total=total,
        por_status=por_status,
        esta_semana=esta_semana,
        este_mes=este_mes,
    )


@router.get("/entrevistas/{entrevista_id}", response_model=EntrevistaResponse)
async def obter_entrevista(
    entrevista_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter entrevista por ID."""
    entrevista = await db.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")
    return entrevista


@router.patch("/entrevistas/{entrevista_id}", response_model=EntrevistaResponse)
async def atualizar_entrevista(
    entrevista_id: uuid.UUID,
    data: EntrevistaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar respostas/status de entrevista."""
    entrevista = await db.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nenhuma alteração enviada")

    status_novo = changes.get("status")
    valid_statuses = {"em_andamento", "submetida", "devolvida", "concluida", "cancelada"}
    if status_novo is not None:
        if status_novo not in valid_statuses:
            raise HTTPException(status_code=400, detail="Status inválido para entrevista")
        transition = (entrevista.status, status_novo)
        allowed_roles = _STATUS_TRANSITIONS.get(transition)
        if allowed_roles is None:
            raise HTTPException(status_code=400, detail=f"Transição {entrevista.status} → {status_novo} não permitida")
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Seu papel não permite esta transição de status")
        if status_novo == "devolvida":
            motivo = changes.get("motivo_devolucao")
            if not motivo or not str(motivo).strip():
                raise HTTPException(status_code=422, detail="motivo_devolucao obrigatório ao devolver")

    # Atribuir/reatribuir cliente (apenas internos)
    novo_cliente_id = changes.get("cliente_id")
    if novo_cliente_id is not None:
        cliente = await db.get(User, novo_cliente_id)
        if not cliente or cliente.role != "cliente":
            raise HTTPException(status_code=422, detail="Usuário informado não possui role cliente")
        if not cliente.is_active:
            raise HTTPException(status_code=422, detail="Usuário cliente está inativo")
        entrevista.cliente_id = novo_cliente_id

    if "respostas" in changes and changes["respostas"] is not None:
        entrevista.respostas = changes["respostas"]

    if "motivo_devolucao" in changes:
        entrevista.motivo_devolucao = changes["motivo_devolucao"]

    if status_novo is not None:
        entrevista.status = status_novo
        if status_novo in {"concluida", "cancelada"}:
            entrevista.completed_at = datetime.now(UTC)
        else:
            entrevista.completed_at = None

    await db.flush()
    await db.refresh(entrevista)
    return entrevista


@router.delete("/entrevistas/{entrevista_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_entrevista(
    entrevista_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir entrevista e suas evidências associadas."""
    entrevista = await db.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")

    await db.delete(entrevista)
    await db.flush()
    return None


@router.get("/entrevistas/{entrevista_id}/evidencias", response_model=list[EvidenciaResponse])
async def listar_evidencias(
    entrevista_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar evidências já anexadas em uma entrevista."""
    entrevista = await db.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")

    result = await db.execute(
        select(Evidencia)
        .where(Evidencia.entrevista_id == entrevista_id)
        .order_by(Evidencia.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/entrevistas/{entrevista_id}/evidencias",
    response_model=EvidenciaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidencia(
    entrevista_id: uuid.UUID,
    file: UploadFile = File(...),
    pergunta_id: uuid.UUID | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enviar anexo com hash SHA-256 para storage S3/MinIO (US-003)."""
    entrevista = await db.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")

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
        f"entrevistas/{entrevista_id}/"
        f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}-{safe_filename}"
    )

    try:
        storage_path = upload_evidencia_bytes(payload, storage_key, file.content_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Falha ao armazenar evidência") from exc

    evidencia = Evidencia(
        entrevista_id=entrevista_id,
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


@router.delete("/entrevistas/{entrevista_id}/evidencias/{evidencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_evidencia(
    entrevista_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir evidência vinculada à entrevista."""
    evidencia = await db.get(Evidencia, evidencia_id)
    if not evidencia or evidencia.entrevista_id != entrevista_id:
        raise HTTPException(status_code=404, detail="Evidência não encontrada")

    await db.delete(evidencia)
    await db.flush()
    return None


@router.get("/evidencias/{evidencia_id}/download")
async def baixar_evidencia(
    evidencia_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Baixar conteúdo de evidência para preview/autenticação via API."""
    evidencia = await db.get(Evidencia, evidencia_id)
    if not evidencia:
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


@router.post(
    "/entrevistas/{entrevista_id}/sugestao-classe",
    response_model=SugestaoClasseResponse,
)
async def gerar_sugestao_classe(
    entrevista_id: uuid.UUID,
    data: SugestaoClasseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Gerar sugestão automática de classe documental (US-004 inicial)."""
    entrevista = await db.get(Entrevista, entrevista_id)
    if not entrevista:
        raise HTTPException(status_code=404, detail="Entrevista não encontrada")

    roteiro = await db.get(Roteiro, entrevista.roteiro_id)
    if not roteiro:
        raise HTTPException(status_code=404, detail="Roteiro não encontrado")

    respostas = entrevista.respostas or {}
    if data.respostas is not None:
        respostas = data.respostas
        entrevista.respostas = data.respostas

    classe, justificativa = suggest_document_class(
        respostas=respostas,
        roteiro_titulo=roteiro.titulo,
        roteiro_area=roteiro.area,
    )

    entrevista.sugestao_classe = classe
    entrevista.sugestao_justificativa = justificativa
    await db.flush()

    return SugestaoClasseResponse(
        entrevista_id=entrevista.id,
        sugestao_classe=classe,
        sugestao_justificativa=justificativa,
    )
