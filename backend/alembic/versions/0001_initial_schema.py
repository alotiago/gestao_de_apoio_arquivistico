"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-03-10 21:50:00
"""

from alembic import op

from app.database import Base
from app.models import *  # noqa: F401,F403

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)