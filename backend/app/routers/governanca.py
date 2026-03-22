"""
Router EP5: Governanca - Matriz de Rastreabilidade e Audit Logs.
"""

import hashlib
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.governanca import MatrizRastreabilidade, AuditLog
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# ===== Schemas =====

class MatrizCreate(BaseModel):
    pcd_nivel_id: uuid.UUID
    legislacao: str
    artigo: str | None = None
    norma_interna: str | None = None
    regra_retencao_id: uuid.UUID | None = None
    risco: str | None = None
    evidencia: str | None = None


class MatrizResponse(BaseModel):
    id: uuid.UUID
    pcd_nivel_id: uuid.UUID
    legislacao: str
    artigo: str | None
    norma_interna: str | None
    regra_retencao_id: uuid.UUID | None
    risco: str | None
    evidencia: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class MatrizUpdate(BaseModel):
    legislacao: str | None = None
    artigo: str | None = None
    norma_interna: str | None = None
    regra_retencao_id: uuid.UUID | None = None
    risco: str | None = None
    evidencia: str | None = None


class AuditLogResponse(BaseModel):
    id: int
    acao: str
    entidade: str
    entidade_id: uuid.UUID | None
    usuario_id: uuid.UUID | None
    ip_address: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


async def _append_audit_log(
    db: AsyncSession,
    *,
    acao: str,
    entidade: str,
    entidade_id: uuid.UUID | None,
    usuario_id: uuid.UUID | None,
    dados_antes: dict | None,
    dados_depois: dict | None,
) -> None:
    logs_result = await db.execute(select(AuditLog))
    logs = logs_result.scalars().all()
    ultimo_hash = logs[-1].hash_atual if logs else None

    payload = {
        "acao": acao,
        "entidade": entidade,
        "entidade_id": str(entidade_id) if entidade_id else None,
        "usuario_id": str(usuario_id) if usuario_id else None,
        "dados_antes": dados_antes,
        "dados_depois": dados_depois,
        "hash_anterior": ultimo_hash,
    }
    hash_atual = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()

    db.add(
        AuditLog(
            hash_anterior=ultimo_hash,
            hash_atual=hash_atual,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            usuario_id=usuario_id,
            dados_antes=dados_antes,
            dados_depois=dados_depois,
            ip_address=None,
            user_agent="api",
        )
    )


# ===== Endpoints — Matriz =====

@router.get("/matriz", response_model=list[MatrizResponse])
async def listar_matriz(
    pcd_nivel_id: uuid.UUID | None = None,
    risco: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar matriz de rastreabilidade (US-040)."""
    query = select(MatrizRastreabilidade)
    if pcd_nivel_id:
        query = query.where(MatrizRastreabilidade.pcd_nivel_id == pcd_nivel_id)
    if risco:
        query = query.where(MatrizRastreabilidade.risco == risco)
    result = await db.execute(query.order_by(MatrizRastreabilidade.created_at.desc()))
    return result.scalars().all()


@router.post("/matriz", response_model=MatrizResponse, status_code=status.HTTP_201_CREATED)
async def criar_entrada_matriz(
    data: MatrizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar entrada na matriz de rastreabilidade (US-040)."""
    entrada = MatrizRastreabilidade(**data.model_dump())
    db.add(entrada)
    await db.flush()
    await _append_audit_log(
        db,
        acao="matriz.create",
        entidade="matriz_rastreabilidade",
        entidade_id=entrada.id,
        usuario_id=current_user.id,
        dados_antes=None,
        dados_depois={
            "legislacao": entrada.legislacao,
            "artigo": entrada.artigo,
            "norma_interna": entrada.norma_interna,
            "risco": entrada.risco,
            "evidencia": entrada.evidencia,
        },
    )
    await db.flush()
    await db.refresh(entrada)
    return entrada


@router.patch("/matriz/{entrada_id}", response_model=MatrizResponse)
async def atualizar_entrada_matriz(
    entrada_id: uuid.UUID,
    data: MatrizUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar entrada da matriz de rastreabilidade."""
    entrada = await db.get(MatrizRastreabilidade, entrada_id)
    if not entrada:
        raise HTTPException(status_code=404, detail="Entrada da matriz não encontrada")

    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nenhuma alteração enviada")

    dados_antes = {
        "legislacao": entrada.legislacao,
        "artigo": entrada.artigo,
        "norma_interna": entrada.norma_interna,
        "risco": entrada.risco,
        "evidencia": entrada.evidencia,
    }
    for field, value in changes.items():
        setattr(entrada, field, value)

    await db.flush()
    await _append_audit_log(
        db,
        acao="matriz.update",
        entidade="matriz_rastreabilidade",
        entidade_id=entrada.id,
        usuario_id=current_user.id,
        dados_antes=dados_antes,
        dados_depois={
            "legislacao": entrada.legislacao,
            "artigo": entrada.artigo,
            "norma_interna": entrada.norma_interna,
            "risco": entrada.risco,
            "evidencia": entrada.evidencia,
        },
    )
    await db.flush()
    await db.refresh(entrada)
    return entrada


@router.delete("/matriz/{entrada_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_entrada_matriz(
    entrada_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir entrada da matriz de rastreabilidade."""
    entrada = await db.get(MatrizRastreabilidade, entrada_id)
    if not entrada:
        raise HTTPException(status_code=404, detail="Entrada da matriz não encontrada")

    dados_antes = {
        "legislacao": entrada.legislacao,
        "artigo": entrada.artigo,
        "norma_interna": entrada.norma_interna,
        "risco": entrada.risco,
        "evidencia": entrada.evidencia,
    }
    await db.delete(entrada)
    await db.flush()

    await _append_audit_log(
        db,
        acao="matriz.delete",
        entidade="matriz_rastreabilidade",
        entidade_id=entrada_id,
        usuario_id=current_user.id,
        dados_antes=dados_antes,
        dados_depois=None,
    )
    await db.flush()
    return None


# ===== Endpoints — Audit Logs =====

@router.get("/logs", response_model=list[AuditLogResponse])
async def listar_logs(
    entidade: str | None = None,
    acao: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar audit logs (somente leitura) (US-041)."""
    query = select(AuditLog)
    if entidade:
        query = query.where(AuditLog.entidade == entidade)
    if acao:
        query = query.where(AuditLog.acao == acao)

    query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/logs/verificar-integridade")
async def verificar_integridade_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verificar integridade da hashchain dos logs (US-041)."""
    result = await db.execute(select(AuditLog).order_by(AuditLog.id))
    logs = result.scalars().all()

    total = len(logs)
    inconsistencias = []

    for i, log in enumerate(logs):
        if i == 0:
            if log.hash_anterior is not None:
                inconsistencias.append({"id": log.id, "erro": "Primeiro log não deveria ter hash_anterior"})
        else:
            if log.hash_anterior != logs[i - 1].hash_atual:
                inconsistencias.append({
                    "id": log.id,
                    "erro": f"hash_anterior ({log.hash_anterior}) != hash_atual do anterior ({logs[i-1].hash_atual})",
                })

    return {
        "total_logs": total,
        "total_inconsistencias": len(inconsistencias),
        "integridade": "OK" if not inconsistencias else "COMPROMETIDA",
        "inconsistencias": inconsistencias[:50],  # Limitar output
    }
