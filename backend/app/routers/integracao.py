"""Router EP6: Integração interna — importação de acervo e operações REST."""

import csv
import io
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.integracao import ImportacaoAcervo
from app.models.pcd import PcdNivel
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


class ImportacaoAcervoResponse(BaseModel):
    id: uuid.UUID
    nome_arquivo: str
    status: str
    mapping: dict
    total_registros: int
    total_sucesso: int
    total_erros: int
    resultados: list[dict] = Field(default_factory=list)
    observacoes: str | None
    criado_por: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


def _parse_mapping(mapping_json: str) -> dict[str, str]:
    try:
        parsed = json.loads(mapping_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="mapping_json inválido") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="mapping_json deve ser um objeto JSON")

    required_fields = {"codigo", "titulo", "classe_codigo"}
    missing = [field for field in required_fields if not parsed.get(field)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Campos obrigatórios do mapping ausentes: {missing}")

    return {str(key): str(value) for key, value in parsed.items()}


async def _mapa_classes_por_codigo(db: AsyncSession) -> dict[str, PcdNivel]:
    result = await db.execute(select(PcdNivel))
    niveis = result.scalars().all()
    return {
        nivel.codigo: nivel
        for nivel in niveis
        if getattr(nivel, "tipo", None) == "classe" and getattr(nivel, "codigo", None)
    }


@router.get("/importacoes", response_model=list[ImportacaoAcervoResponse])
async def listar_importacoes(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar importações de acervo processadas (US-052)."""
    query = select(ImportacaoAcervo)
    if status_filter:
        query = query.where(ImportacaoAcervo.status == status_filter)
    result = await db.execute(query.order_by(ImportacaoAcervo.created_at.desc()))
    return result.scalars().all()


@router.get("/importacoes/{importacao_id}", response_model=ImportacaoAcervoResponse)
async def obter_importacao(
    importacao_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter detalhes de uma importação de acervo (US-052)."""
    item = await db.get(ImportacaoAcervo, importacao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    return item


@router.post("/importacoes", response_model=ImportacaoAcervoResponse, status_code=status.HTTP_201_CREATED)
async def importar_acervo_csv(
    arquivo: UploadFile = File(...),
    mapping_json: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Importar inventário CSV com mapeamento de campos e validação de erros/sucessos (US-052)."""
    if not arquivo.filename:
        raise HTTPException(status_code=400, detail="Arquivo não informado")
    if not arquivo.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Somente arquivos CSV são suportados")

    mapping = _parse_mapping(mapping_json)
    payload = await arquivo.read()
    try:
        csv_text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV deve estar codificado em UTF-8") from exc

    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV sem cabeçalho")

    headers = set(reader.fieldnames)
    missing_columns = [column for column in mapping.values() if column and column not in headers]
    if missing_columns:
        raise HTTPException(status_code=400, detail=f"Colunas do mapping não encontradas no CSV: {missing_columns}")

    classes = await _mapa_classes_por_codigo(db)
    resultados: list[dict] = []
    total_sucesso = 0
    total_erros = 0

    for line_number, row in enumerate(reader, start=2):
        codigo = (row.get(mapping["codigo"]) or "").strip()
        titulo = (row.get(mapping["titulo"]) or "").strip()
        classe_codigo = (row.get(mapping["classe_codigo"]) or "").strip()
        descricao = (row.get(mapping.get("descricao", "")) or "").strip() if mapping.get("descricao") else None

        erros: list[str] = []
        if not codigo:
            erros.append("codigo ausente")
        if not titulo:
            erros.append("titulo ausente")
        if not classe_codigo:
            erros.append("classe_codigo ausente")
        elif classe_codigo not in classes:
            erros.append(f"classe_codigo '{classe_codigo}' não encontrada no PCD")

        if erros:
            total_erros += 1
            resultados.append(
                {
                    "linha": line_number,
                    "status": "erro",
                    "codigo": codigo or None,
                    "titulo": titulo or None,
                    "classe_codigo": classe_codigo or None,
                    "erros": erros,
                }
            )
            continue

        total_sucesso += 1
        resultados.append(
            {
                "linha": line_number,
                "status": "sucesso",
                "codigo": codigo,
                "titulo": titulo,
                "classe_codigo": classe_codigo,
                "classe_id": str(classes[classe_codigo].id),
                "descricao": descricao,
            }
        )

    total_registros = total_sucesso + total_erros
    status_importacao = "processado" if total_erros == 0 else "concluido_com_erros"
    importacao = ImportacaoAcervo(
        nome_arquivo=arquivo.filename,
        status=status_importacao,
        mapping=mapping,
        total_registros=total_registros,
        total_sucesso=total_sucesso,
        total_erros=total_erros,
        resultados=resultados,
        observacoes="Importação concluída" if total_erros == 0 else "Importação concluída com inconsistências",
        criado_por=current_user.id,
    )
    db.add(importacao)
    await db.flush()
    await db.refresh(importacao)
    return importacao


@router.post("/importacoes/{importacao_id}/reprocessar", response_model=ImportacaoAcervoResponse, status_code=status.HTTP_201_CREATED)
async def reprocessar_importacao(
    importacao_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reprocessar importação existente reaplicando mapping/resultados registrados."""
    origem = await db.get(ImportacaoAcervo, importacao_id)
    if not origem:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    if origem.status == "excluida":
        raise HTTPException(status_code=400, detail="Importação excluída não pode ser reprocessada")

    clone = ImportacaoAcervo(
        nome_arquivo=origem.nome_arquivo,
        status=origem.status,
        mapping=dict(origem.mapping or {}),
        total_registros=origem.total_registros,
        total_sucesso=origem.total_sucesso,
        total_erros=origem.total_erros,
        resultados=list(origem.resultados or []),
        observacoes=f"Reprocessada a partir de {origem.id}",
        criado_por=current_user.id,
    )
    db.add(clone)
    await db.flush()
    await db.refresh(clone)
    return clone


@router.delete("/importacoes/{importacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_importacao(
    importacao_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir logicamente importação sem sucesso persistido."""
    item = await db.get(ImportacaoAcervo, importacao_id)
    if not item:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    if item.total_sucesso > 0:
        raise HTTPException(status_code=400, detail="Importação com registros de sucesso não pode ser excluída")

    item.status = "excluida"
    await db.flush()
    return None
