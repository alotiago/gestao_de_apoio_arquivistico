"""
Router EP3: Tabela de Temporalidade e Destinação (TTD).
"""

import hashlib
import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ttd import RegraRetencao, LegalHold, OrdemDestinacao
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter()


# ===== Schemas =====

class RegraRetencaoCreate(BaseModel):
    pcd_nivel_id: uuid.UUID
    evento_inicio: str
    prazo_dias: int
    fase_corrente: int = 0
    fase_intermediaria: int = 0
    destinacao_final: str  # eliminacao, guarda_permanente, microfilmagem
    base_legal: str | None = None
    legislacao_ref: str | None = None
    observacoes: str | None = None


class RegraRetencaoResponse(BaseModel):
    id: uuid.UUID
    pcd_nivel_id: uuid.UUID
    evento_inicio: str
    prazo_dias: int
    fase_corrente: int
    fase_intermediaria: int
    destinacao_final: str
    base_legal: str | None
    legislacao_ref: str | None
    observacoes: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class LegalHoldCreate(BaseModel):
    pcd_nivel_id: uuid.UUID
    motivo: str
    tipo: str  # litigio, investigacao, auditoria, regulatorio
    data_expiracao: datetime | None = None
    evidencia: str | None = None


class LegalHoldResponse(BaseModel):
    id: uuid.UUID
    pcd_nivel_id: uuid.UUID
    motivo: str
    tipo: str
    aplicado_por: uuid.UUID
    data_inicio: datetime
    data_expiracao: datetime | None
    status: str
    evidencia: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class OrdemDestinacaoCreate(BaseModel):
    tipo: str
    items: list[dict] = Field(default_factory=list)


class OrdemDestinacaoResponse(BaseModel):
    id: uuid.UUID
    tipo: str
    status: str
    aprovador_1_id: uuid.UUID | None
    aprovador_2_id: uuid.UUID | None
    hash_termo: str | None
    assinatura_digital: str | None
    carimbo_tempo: datetime | None
    items: list[dict]
    created_at: datetime
    executada_em: datetime | None
    model_config = {"from_attributes": True}


class AssinarOrdemPayload(BaseModel):
    assinatura_digital: str | None = None


# ===== Endpoints — Regras de Retenção =====

@router.get("/regras", response_model=list[RegraRetencaoResponse])
async def listar_regras(
    pcd_nivel_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar regras de retenção (US-020)."""
    query = select(RegraRetencao)
    if pcd_nivel_id:
        query = query.where(RegraRetencao.pcd_nivel_id == pcd_nivel_id)
    result = await db.execute(query.order_by(RegraRetencao.created_at.desc()))
    return result.scalars().all()


@router.post("/regras", response_model=RegraRetencaoResponse, status_code=status.HTTP_201_CREATED)
async def criar_regra(
    data: RegraRetencaoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar regra de retenção com evento de início (US-020)."""
    regra = RegraRetencao(**data.model_dump())
    db.add(regra)
    await db.flush()
    await db.refresh(regra)
    return regra


@router.get("/regras/{regra_id}", response_model=RegraRetencaoResponse)
async def obter_regra(
    regra_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obter regra por ID."""
    regra = await db.get(RegraRetencao, regra_id)
    if not regra:
        raise HTTPException(status_code=404, detail="Regra não encontrada")
    return regra


# ===== Endpoints — Legal Holds =====

@router.get("/holds", response_model=list[LegalHoldResponse])
async def listar_holds(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar legal holds (US-021)."""
    query = select(LegalHold)
    if status_filter:
        query = query.where(LegalHold.status == status_filter)
    result = await db.execute(query.order_by(LegalHold.created_at.desc()))
    return result.scalars().all()


@router.post("/holds", response_model=LegalHoldResponse, status_code=status.HTTP_201_CREATED)
async def aplicar_hold(
    data: LegalHoldCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aplicar legal hold em um nível do PCD (US-021)."""
    hold = LegalHold(
        **data.model_dump(),
        aplicado_por=current_user.id,
    )
    db.add(hold)
    await db.flush()
    await db.refresh(hold)
    return hold


@router.patch("/holds/{hold_id}/revogar", response_model=LegalHoldResponse)
async def revogar_hold(
    hold_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revogar um legal hold (US-021)."""
    hold = await db.get(LegalHold, hold_id)
    if not hold:
        raise HTTPException(status_code=404, detail="Hold não encontrado")
    if hold.status != "ativo":
        raise HTTPException(status_code=400, detail="Hold já não está ativo")

    hold.status = "revogado"
    await db.flush()
    await db.refresh(hold)
    return hold


@router.get("/ordens", response_model=list[OrdemDestinacaoResponse])
async def listar_ordens(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(OrdemDestinacao)
    if status_filter:
        query = query.where(OrdemDestinacao.status == status_filter)
    result = await db.execute(query.order_by(OrdemDestinacao.created_at.desc()))
    return result.scalars().all()


@router.post("/ordens", response_model=OrdemDestinacaoResponse, status_code=status.HTTP_201_CREATED)
async def criar_ordem(
    data: OrdemDestinacaoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tipos_validos = {"eliminacao", "transferencia", "recolhimento"}
    if data.tipo not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido: {data.tipo}")

    ordem = OrdemDestinacao(
        tipo=data.tipo,
        status="pendente",
        items=data.items,
    )
    db.add(ordem)
    await db.flush()
    await db.refresh(ordem)
    return ordem


@router.patch("/ordens/{ordem_id}/aprovar", response_model=OrdemDestinacaoResponse)
async def aprovar_ordem(
    ordem_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ordem = await db.get(OrdemDestinacao, ordem_id)
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")

    if ordem.status not in {"pendente", "em_aprovacao"}:
        raise HTTPException(status_code=400, detail="Ordem não está em etapa de aprovação")

    if ordem.aprovador_1_id is None:
        ordem.aprovador_1_id = current_user.id
        ordem.status = "em_aprovacao"
    elif ordem.aprovador_2_id is None:
        if ordem.aprovador_1_id == current_user.id:
            raise HTTPException(status_code=400, detail="Segundo aprovador deve ser diferente do primeiro")
        ordem.aprovador_2_id = current_user.id
        ordem.status = "aprovado"
    else:
        raise HTTPException(status_code=400, detail="Ordem já possui duas aprovações")

    await db.flush()
    await db.refresh(ordem)
    return ordem


@router.patch("/ordens/{ordem_id}/assinar", response_model=OrdemDestinacaoResponse)
async def assinar_ordem(
    ordem_id: uuid.UUID,
    data: AssinarOrdemPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ordem = await db.get(OrdemDestinacao, ordem_id)
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")

    if ordem.status != "aprovado":
        raise HTTPException(status_code=400, detail="Ordem precisa estar aprovada para assinatura")

    payload_hash = {
        "ordem_id": str(ordem.id),
        "tipo": ordem.tipo,
        "items": ordem.items,
        "aprovador_1_id": str(ordem.aprovador_1_id) if ordem.aprovador_1_id else None,
        "aprovador_2_id": str(ordem.aprovador_2_id) if ordem.aprovador_2_id else None,
        "assinado_por": str(current_user.id),
    }
    payload_serializado = json.dumps(payload_hash, ensure_ascii=False, sort_keys=True)
    ordem.hash_termo = hashlib.sha256(payload_serializado.encode("utf-8")).hexdigest()
    ordem.assinatura_digital = data.assinatura_digital or f"ASS-{uuid.uuid4()}"
    ordem.carimbo_tempo = datetime.now(UTC)
    ordem.status = "assinado"

    await db.flush()
    await db.refresh(ordem)
    return ordem
