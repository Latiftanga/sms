"""Add motto column to school table

Revision ID: 20250527_005
Revises: 20250527_004
Create Date: 2025-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("school", sa.Column("motto", sa.String(300), nullable=True))


def downgrade() -> None:
    op.drop_column("school", "motto")
