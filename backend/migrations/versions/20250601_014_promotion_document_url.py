"""Add document_url to staff_promotion

Revision ID: 20250601_014
Revises: 20250531_013
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "20250601_014"
down_revision = "20250531_013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("staff_promotion", sa.Column("document_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("staff_promotion", "document_url")
