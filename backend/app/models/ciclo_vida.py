"""
Models EP4: Ciclo de Vida — Jobs de Retenção e Workflows.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobRetencao(Base):
    """Jobs programados de análise de prazos e geração de ordens (US-030)."""
    __tablename__ = "jobs_retencao"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    janela_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    janela_fim: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="agendado")  # agendado, executando, concluido, falha
    total_analisados: Mapped[int] = mapped_column(Integer, default=0)
    total_ordens: Mapped[int] = mapped_column(Integer, default=0)
    log_execucao: Mapped[dict] = mapped_column(JSONB, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<JobRetencao [{self.status}] {self.total_analisados} analisados>"


class WorkflowTarefa(Base):
    """Tarefas de workflow de avaliação e aprovação (US-031)."""
    __tablename__ = "workflow_tarefas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # avaliacao, aprovacao, execucao
    estado: Mapped[str] = mapped_column(
        String(30), default="pendente", index=True
    )  # pendente, em_avaliacao, aprovado, rejeitado, executado
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    item_tipo: Mapped[str] = mapped_column(String(50), nullable=False)  # ordem_destinacao, pcd_nivel, etc
    atribuido_a: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    sla_horas: Mapped[int] = mapped_column(Integer, default=72)
    comentario: Mapped[str | None] = mapped_column(Text)
    escalado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<WorkflowTarefa [{self.tipo}] {self.estado}>"


class SeloEvidencia(Base):
    """Selo de evidência com hash e metadados para comprovação de integridade (US-032)."""
    __tablename__ = "selos_evidencia"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entidade: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # job_retencao, workflow_tarefa, ordem_destinacao
    entidade_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    razao: Mapped[str] = mapped_column(Text, nullable=False)
    criado_por: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    hash_selo: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    carimbo_tempo: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadados: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<SeloEvidencia [{self.entidade}] {self.hash_selo[:12]}>"


class EventoInterno(Base):
    """Eventos internos com payload assinado para sincronização entre módulos (US-051)."""
    __tablename__ = "eventos_internos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    origem: Mapped[str] = mapped_column(String(100), nullable=False)
    referencia_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    assinatura: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="enviado", index=True)  # pendente, enviado, falha
    tentativas: Mapped[int] = mapped_column(Integer, default=1)
    proxima_tentativa: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enviado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<EventoInterno [{self.tipo}] {self.status}>"
