"""Add cliente_id and motivo_devolucao to entrevistas

Revision ID: 0002_add_entrevista_cliente_fields
Revises: 0001_initial_schema
Create Date: 2026-03-21 12:00:00
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_cliente_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return result.scalar() is not None


def upgrade() -> None:
    if not _column_exists("entrevistas", "cliente_id"):
        op.add_column(
            "entrevistas",
            sa.Column("cliente_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        )
    if not _column_exists("entrevistas", "motivo_devolucao"):
        op.add_column(
            "entrevistas",
            sa.Column("motivo_devolucao", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("entrevistas", "motivo_devolucao"):
        op.drop_column("entrevistas", "motivo_devolucao")
    if _column_exists("entrevistas", "cliente_id"):
        op.drop_column("entrevistas", "cliente_id")
