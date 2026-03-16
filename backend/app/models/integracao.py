"""Models EP6: Integração interna e importação de acervo."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ImportacaoAcervo(Base):
    """Registro de importação interna de acervo a partir de CSV (US-052)."""
    __tablename__ = "importacoes_acervo"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="processado", index=True)  # processado, concluido_com_erros, falha
    mapping: Mapped[dict] = mapped_column(JSONB, default=dict)
    total_registros: Mapped[int] = mapped_column(Integer, default=0)
    total_sucesso: Mapped[int] = mapped_column(Integer, default=0)
    total_erros: Mapped[int] = mapped_column(Integer, default=0)
    resultados: Mapped[list] = mapped_column(JSONB, default=list)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<ImportacaoAcervo [{self.status}] {self.total_sucesso}/{self.total_registros}>"
