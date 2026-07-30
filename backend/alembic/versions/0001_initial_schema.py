"""Initial complete Nova schema.

Revision ID: 0001_initial
Revises: None
Create Date: 2026-07-26
"""
from alembic import op

from app.database.base import Base
from app.models import entities  # noqa: F401

revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
