"""Add attendance_mode to school

DAILY  — one roll call per day, taken by the designated class teacher.
LESSON — attendance captured per lesson period by the subject teacher.

Revision ID: 20250529_011
Revises: 20250528_010
Create Date: 2025-05-29
"""
import sqlalchemy as sa
from alembic import op

revision = "20250529_011"
down_revision = "20250528_010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "school",
        sa.Column(
            "attendance_mode",
            sa.String(10),
            nullable=False,
            server_default="DAILY",
        ),
    )


def downgrade() -> None:
    op.drop_column("school", "attendance_mode")
