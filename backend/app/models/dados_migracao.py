"""Models EP9: inventário e qualidade de dados para migração."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RegraCleansing(Base):
    """Regra de cleansing aplicável a inventários de qualidade (US-080)."""

    __tablename__ = "regras_cleansing"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    campo: Mapped[str | None] = mapped_column(String(80))
    configuracao: Mapped[dict] = mapped_column(JSONB, default=dict)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<RegraCleansing {self.tipo} campo={self.campo or '*'}>"


class InventarioQualidade(Base):
    """Snapshot de score de qualidade derivado de um acervo importado (US-080)."""

    __tablename__ = "inventarios_qualidade"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    importacao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("importacoes_acervo.id"), index=True)
    total_registros: Mapped[int] = mapped_column(default=0)
    score_geral: Mapped[float] = mapped_column(Float, default=0)
    score_completude: Mapped[float] = mapped_column(Float, default=0)
    score_unicidade: Mapped[float] = mapped_column(Float, default=0)
    score_conformidade: Mapped[float] = mapped_column(Float, default=0)
    status_qualidade: Mapped[str] = mapped_column(String(30), default="critico", index=True)
    regras_aplicadas: Mapped[list] = mapped_column(JSONB, default=list)
    indicadores: Mapped[dict] = mapped_column(JSONB, default=dict)
    inconsistencias: Mapped[list] = mapped_column(JSONB, default=list)
    recomendacoes: Mapped[list] = mapped_column(JSONB, default=list)
    comparativo_anterior: Mapped[dict | None] = mapped_column(JSONB)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<InventarioQualidade {self.status_qualidade} score={self.score_geral:.2f}>"


class OndaMigracao(Base):
    """Planejamento de migração por ondas com histórico operacional (US-081)."""

    __tablename__ = "ondas_migracao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    unidade: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    processo: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    ordem: Mapped[int] = mapped_column(default=1, index=True)
    status: Mapped[str] = mapped_column(String(30), default="planejada", index=True)
    estrategia_corte: Mapped[str] = mapped_column(String(30), default="ondas")
    data_corte_planejada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inventario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inventarios_qualidade.id"), index=True)
    historico: Mapped[list] = mapped_column(JSONB, default=list)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<OndaMigracao ordem={self.ordem} status={self.status}>"


class FaseMigracao(Base):
    """Fase pertencente a uma onda de migração planejada (US-081)."""

    __tablename__ = "fases_migracao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    onda_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ondas_migracao.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    ordem: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(30), default="planejada", index=True)
    rollback_script: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<FaseMigracao {self.nome} status={self.status}>"


class DependenciaMigracao(Base):
    """Dependência entre ondas para liberação de execução (US-081)."""

    __tablename__ = "dependencias_migracao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    onda_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ondas_migracao.id"), index=True)
    depende_de_onda_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ondas_migracao.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(30), default="finish_to_start")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<DependenciaMigracao {self.onda_id}<-{self.depende_de_onda_id}>"
