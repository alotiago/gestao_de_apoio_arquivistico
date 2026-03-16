"""
Router EP5: Governança — Matriz de Rastreabilidade e Audit Logs.
"""

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


class AuditLogResponse(BaseModel):
    id: int
    acao: str
    entidade: str
    entidade_id: uuid.UUID | None
    usuario_id: uuid.UUID | None
    ip_address: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


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
    await db.refresh(entrada)
    return entrada


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
