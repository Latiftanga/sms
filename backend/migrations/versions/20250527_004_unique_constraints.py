"""Add unique constraints to academic_year, academic_term, and class

Revision ID: 004
Revises: 003
Create Date: 2025-05-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_academic_year_school_name",
        "academic_year",
        ["school_id", "name"],
    )
    op.create_unique_constraint(
        "uq_academic_term_year_name",
        "academic_term",
        ["academic_year_id", "name"],
    )
    op.create_unique_constraint(
        "uq_class_identity",
        "class",
        ["school_id", "level", "year", "learning_area_id", "stream"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_class_identity", "class", type_="unique")
    op.drop_constraint("uq_academic_term_year_name", "academic_term", type_="unique")
    op.drop_constraint("uq_academic_year_school_name", "academic_year", type_="unique")
