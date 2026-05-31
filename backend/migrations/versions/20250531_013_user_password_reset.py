"""Add password_reset_token and password_reset_expires_at to user table.

Revision ID: 20250531_013
Revises: 20250529_012
Create Date: 2025-05-31
"""
import sqlalchemy as sa
from alembic import op

revision = "20250531_013"
down_revision = "20250529_012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user", sa.Column("password_reset_token", sa.String(100), nullable=True))
    op.add_column("user", sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint("uq_user_password_reset_token", "user", ["password_reset_token"])


def downgrade() -> None:
    op.drop_constraint("uq_user_password_reset_token", "user", type_="unique")
    op.drop_column("user", "password_reset_expires_at")
    op.drop_column("user", "password_reset_token")
