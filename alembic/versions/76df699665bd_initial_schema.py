"""initial schema

Revision ID: 76df699665bd
Revises: 
Create Date: 2026-11-10 12:23:55.344509

Baseline migration: creates the current SkyCast schema from SQLAlchemy metadata.
For databases already initialized via `create_all`, run `alembic stamp head`.
"""
from typing import Sequence, Union

from alembic import op

from app.db.base import Base
import app.db.models  # noqa: F401  (register all models)

# revision identifiers, used by Alembic.
revision: str = "76df699665bd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
