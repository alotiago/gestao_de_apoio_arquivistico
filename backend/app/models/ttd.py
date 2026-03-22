"""
Models EP3: Tabela de Temporalidade e Destinação (TTD).
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RegraRetencao(Base):
    """Regras de retenção com eventos de início e prazos (US-020)."""
    __tablename__ = "regras_retencao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pcd_nivel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pcd_niveis.id"), nullable=False, index=True
    )
    evento_inicio: Mapped[str] = mapped_column(String(100), nullable=False)  # fim_contrato, rescisao, prescricao
    prazo_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    fase_corrente: Mapped[int] = mapped_column(Integer, default=0)  # anos na fase corrente
    fase_intermediaria: Mapped[int] = mapped_column(Integer, default=0)  # anos na fase intermediária
    destinacao_final: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # eliminacao, guarda_permanente, microfilmagem, amostragem
    base_legal: Mapped[str | None] = mapped_column(Text)
    legislacao_ref: Mapped[str | None] = mapped_column(String(200))
    observacoes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<RegraRetencao '{self.evento_inicio}' +{self.prazo_dias}d → {self.destinacao_final}>"


class LegalHold(Base):
    """Legal holds e exceções para suspensão de prazos (US-021)."""
    __tablename__ = "legal_holds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pcd_nivel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pcd_niveis.id"))
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # litigio, investigacao, auditoria, regulatorio
    aplicado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    data_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data_expiracao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="ativo", index=True)  # ativo, expirado, revogado
    evidencia: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<LegalHold [{self.tipo}] ({self.status})>"


class OrdemDestinacao(Base):
    """Ordens de eliminação/transferência com assinatura digital (US-022)."""
    __tablename__ = "ordens_destinacao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # eliminacao, transferencia, recolhimento
    status: Mapped[str] = mapped_column(String(30), default="pendente")
    # Aprovação 4-olhos
    aprovador_1_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    aprovador_2_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    # Selo digital
    hash_termo: Mapped[str | None] = mapped_column(String(64))
    assinatura_digital: Mapped[str | None] = mapped_column(Text)
    carimbo_tempo: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Itens da ordem
    items: Mapped[dict] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    executada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<OrdemDestinacao [{self.tipo}] ({self.status})>"
