"""
Models EP2: Plano de Classificação de Documentos (PCD).
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PcdNivel(Base):
    """Nível hierárquico do PCD: Função > Atividade > Série > Classe (US-010)."""
    __tablename__ = "pcd_niveis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pai_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pcd_niveis.id"), nullable=True, index=True
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # funcao, subfuncao, atividade, serie, classe, tipo_documental
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    codigo_conarq: Mapped[str | None] = mapped_column(String(50))
    versao: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="rascunho")  # rascunho, ativo, arquivado
    nivel_sigilo: Mapped[str] = mapped_column(String(20), default="publico")  # publico, restrito, confidencial, secreto
    responsavel_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    metadados: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    filhos: Mapped[list["PcdNivel"]] = relationship(back_populates="pai", cascade="all, delete-orphan")
    pai: Mapped["PcdNivel | None"] = relationship(back_populates="filhos", remote_side="PcdNivel.id")
    versoes: Mapped[list["PcdVersao"]] = relationship(back_populates="pcd_nivel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PcdNivel [{self.tipo}] {self.codigo} — {self.titulo}>"


class PcdVersao(Base):
    """Versionamento do PCD com workflow de aprovação (US-011)."""
    __tablename__ = "pcd_versoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pcd_nivel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pcd_niveis.id", ondelete="CASCADE"))
    versao: Mapped[int] = mapped_column(Integer, nullable=False)
    dados_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    aprovado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pendente")  # pendente, aprovado, rejeitado
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pcd_nivel: Mapped["PcdNivel"] = relationship(back_populates="versoes")

    def __repr__(self) -> str:
        return f"<PcdVersao v{self.versao} ({self.status})>"
