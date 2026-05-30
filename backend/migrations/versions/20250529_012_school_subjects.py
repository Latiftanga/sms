"""Add school_subject table — school-wide subject catalogue.

Classes assign subjects from this list rather than using free text.

Revision ID: 20250529_012
Revises: 20250529_011
Create Date: 2025-05-29
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20250529_012"
down_revision = "20250529_011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "school_subject",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(["school_id"], ["school.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "name", name="uq_school_subject_name"),
    )
    op.create_index("ix_school_subject_school_id", "school_subject", ["school_id"])


def downgrade() -> None:
    op.drop_index("ix_school_subject_school_id", table_name="school_subject")
    op.drop_table("school_subject")
