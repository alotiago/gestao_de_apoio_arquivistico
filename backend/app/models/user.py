"""
Model: User — Usuários do sistema com roles e atributos RBAC/ABAC.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="viewer"
    )  # admin, gestor, arquivista, classificador, auditor, viewer
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    departamento: Mapped[str | None] = mapped_column(String(100))
    unidade: Mapped[str | None] = mapped_column(String(100))
    atributos: Mapped[dict] = mapped_column(JSONB, default=dict)  # ABAC attributes
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
