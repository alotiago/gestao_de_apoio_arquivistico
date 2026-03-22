"""Models EP10: base de conhecimento com templates e trilhas persistidas."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TemplateConhecimento(Base):
    """Template/guia oficial de conhecimento para operação interna."""

    __tablename__ = "templates_conhecimento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(80), nullable=False, default="Geral")
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, default=list)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    guide_content: Mapped[str] = mapped_column(Text, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TrilhaConhecimento(Base):
    """Trilha de onboarding por perfil com etapas ordenadas."""

    __tablename__ = "trilhas_conhecimento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(180), nullable=False)
    perfil: Mapped[str] = mapped_column(String(80), nullable=False, default="Geral")
    duracao_estimada_min: Mapped[int] = mapped_column(Integer, default=60)
    etapas: Mapped[list] = mapped_column(JSONB, default=list)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TrilhaProgresso(Base):
    """Progresso individual de usuário em uma trilha."""

    __tablename__ = "trilhas_progresso"
    __table_args__ = (UniqueConstraint("user_id", "trilha_id", name="uq_trilhas_progresso_user_trilha"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    trilha_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trilhas_conhecimento.id"), nullable=False, index=True)
    etapas_concluidas: Mapped[int] = mapped_column(Integer, default=0)
    badge_emitido: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
