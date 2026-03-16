"""
Models EP1: Roteiros, Perguntas, Condições, Entrevistas, Evidências.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Boolean, Text, BigInteger, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Roteiro(Base):
    """Catálogo de roteiros de entrevista dinâmicos (US-001)."""
    __tablename__ = "roteiros"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    area: Mapped[str | None] = mapped_column(String(100))
    versao: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="rascunho")  # rascunho, ativo, arquivado
    versao_pai_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roteiros.id"), nullable=True
    )
    motivo_versao: Mapped[str | None] = mapped_column(Text)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    perguntas: Mapped[list["Pergunta"]] = relationship(back_populates="roteiro", cascade="all, delete-orphan", order_by="Pergunta.ordem")
    versao_pai: Mapped["Roteiro | None"] = relationship(remote_side="Roteiro.id")
    entrevistas: Mapped[list["Entrevista"]] = relationship(back_populates="roteiro")

    def __repr__(self) -> str:
        return f"<Roteiro '{self.titulo}' v{self.versao} ({self.status})>"


class Pergunta(Base):
    """Perguntas de um roteiro com metadado alvo (US-001/US-002)."""
    __tablename__ = "perguntas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roteiro_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roteiros.id", ondelete="CASCADE"))
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # texto, numero, select, multi_select, boolean
    obrigatoria: Mapped[bool] = mapped_column(Boolean, default=True)
    secao: Mapped[str | None] = mapped_column(String(100))
    metadado_alvo: Mapped[str | None] = mapped_column(String(50))  # classe, evento, base_legal, risco, sigilo
    opcoes: Mapped[dict | None] = mapped_column(JSONB)  # para select/multi_select
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    roteiro: Mapped["Roteiro"] = relationship(back_populates="perguntas")
    condicoes: Mapped[list["Condicao"]] = relationship(back_populates="pergunta", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pergunta #{self.ordem} '{self.texto[:40]}...'>"


class Condicao(Base):
    """Condições de branching (IF/ELSE) entre perguntas (US-002)."""
    __tablename__ = "condicoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pergunta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("perguntas.id", ondelete="CASCADE"))
    operador: Mapped[str] = mapped_column(String(10), nullable=False)  # AND, OR, NOT, EQ, NEQ, GT, LT
    valor: Mapped[dict] = mapped_column(JSONB, nullable=False)
    acao: Mapped[str] = mapped_column(String(30), nullable=False)  # mostrar, ocultar, pular_para, obrigar
    alvo_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # ID da pergunta/seção alvo
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pergunta: Mapped["Pergunta"] = relationship(back_populates="condicoes")

    def __repr__(self) -> str:
        return f"<Condicao {self.operador} → {self.acao}>"


class Entrevista(Base):
    """Execução de uma entrevista com respostas e sugestões (US-002/US-004)."""
    __tablename__ = "entrevistas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    roteiro_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roteiros.id"))
    entrevistador_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="em_andamento")  # em_andamento, concluida, cancelada
    respostas: Mapped[dict] = mapped_column(JSONB, default=dict)
    sugestao_classe: Mapped[str | None] = mapped_column(String(100))
    sugestao_justificativa: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    roteiro: Mapped["Roteiro"] = relationship(back_populates="entrevistas")
    evidencias: Mapped[list["Evidencia"]] = relationship(back_populates="entrevista", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Entrevista {self.id} ({self.status})>"


class Evidencia(Base):
    """Evidências e anexos vinculados a entrevistas (US-003)."""
    __tablename__ = "evidencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entrevista_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entrevistas.id", ondelete="CASCADE"))
    pergunta_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("perguntas.id"))
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    entrevista: Mapped["Entrevista"] = relationship(back_populates="evidencias")

    def __repr__(self) -> str:
        return f"<Evidencia '{self.nome_arquivo}' hash={self.hash_sha256[:12]}...>"
