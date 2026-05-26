"""Restructure class table + add learning_area

- Drop year_group + name from class (name is now computed)
- Add level (Creche/Nursery/KG/Basic/SHS) and year (nullable) to class
- Add learning_area table (SHS schools only)
- Add learning_area_id FK on class

Revision ID: 003
Revises: 002
Create Date: 2025-05-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── learning_area ────────────────────────────────────────────────
    op.create_table(
        "learning_area",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("short_name", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("school_id", "name", name="uq_learning_area_school_name"),
    )
    op.create_index("ix_learning_area_school_id", "learning_area", ["school_id"])

    # ── alter class ───────────────────────────────────────────────────
    # Add new columns
    op.add_column("class", sa.Column("level", sa.String(30), nullable=True))
    op.add_column("class", sa.Column("year", sa.Integer, nullable=True))
    op.add_column("class", sa.Column(
        "learning_area_id",
        postgresql.UUID(as_uuid=True),
        sa.ForeignKey("learning_area.id", ondelete="RESTRICT"),
        nullable=True,
    ))

    # Migrate existing year_group data into level + year (best-effort, dev only)
    # e.g. "Basic 4" → level="Basic", year=4 | "Creche" → level="Creche", year=NULL
    op.execute(sa.text("""
        UPDATE "class"
        SET
            level = CASE
                WHEN year_group ~* '^(creche)$'          THEN 'Creche'
                WHEN year_group ~* '^nursery'             THEN 'Nursery'
                WHEN year_group ~* '^kg'                  THEN 'KG'
                WHEN year_group ~* '^(basic|primary|jhs)' THEN 'Basic'
                WHEN year_group ~* '^shs'                 THEN 'SHS'
                ELSE year_group
            END,
            year = NULLIF(
                regexp_replace(year_group, '[^0-9]', '', 'g'), ''
            )::integer
        WHERE year_group IS NOT NULL
    """))

    # Make level NOT NULL now that data is migrated
    op.alter_column("class", "level", nullable=False,
                    server_default=sa.text("'Basic'"))
    op.alter_column("class", "level", server_default=None)

    # Drop old columns
    op.drop_column("class", "name")
    op.drop_column("class", "year_group")


def downgrade() -> None:
    op.add_column("class", sa.Column("year_group", sa.String(20), nullable=True))
    op.add_column("class", sa.Column("name", sa.String(80), nullable=True))
    op.execute(sa.text("""
        UPDATE "class"
        SET year_group = CASE
            WHEN year IS NOT NULL THEN level || ' ' || year::text
            ELSE level
        END,
        name = CASE
            WHEN year IS NOT NULL THEN level || ' ' || year::text
            ELSE level
        END
    """))
    op.drop_column("class", "learning_area_id")
    op.drop_column("class", "year")
    op.drop_column("class", "level")
    op.drop_index("ix_learning_area_school_id", table_name="learning_area")
    op.drop_table("learning_area")
