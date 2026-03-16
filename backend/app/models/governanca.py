"""
Models EP5: Governança — Matriz de Rastreabilidade e Audit Logs.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, BigInteger, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MatrizRastreabilidade(Base):
    """Matriz Classe ↔ Regra ↔ Base Legal ↔ Risco ↔ Evidência (US-040)."""
    __tablename__ = "matriz_rastreabilidade"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pcd_nivel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pcd_niveis.id"))
    legislacao: Mapped[str] = mapped_column(Text, nullable=False)
    artigo: Mapped[str | None] = mapped_column(String(100))
    norma_interna: Mapped[str | None] = mapped_column(String(200))
    regra_retencao_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("regras_retencao.id"))
    risco: Mapped[str | None] = mapped_column(String(20))  # baixo, medio, alto, critico
    evidencia: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<MatrizRastreabilidade risco={self.risco}>"


class AuditLog(Base):
    """Logs imutáveis com hashchain para auditoria (US-041)."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hash_anterior: Mapped[str | None] = mapped_column(String(64))
    hash_atual: Mapped[str] = mapped_column(String(64), nullable=False)
    acao: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entidade: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entidade_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    dados_antes: Mapped[dict | None] = mapped_column(JSONB)
    dados_depois: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<AuditLog [{self.acao}] {self.entidade}:{self.entidade_id}>"
