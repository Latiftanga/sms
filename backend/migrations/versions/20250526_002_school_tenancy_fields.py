"""Add school tenancy, identity and branding fields

Revision ID: 002
Revises: 001
Create Date: 2025-05-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("school", sa.Column("subdomain", sa.String(63), nullable=True))
    op.add_column("school", sa.Column("custom_domain", sa.String(253), nullable=True))
    op.add_column("school", sa.Column("emis_number", sa.String(20), nullable=True))
    op.add_column("school", sa.Column("waec_centre_number", sa.String(20), nullable=True))
    op.add_column("school", sa.Column("ownership_type", sa.String(20), nullable=False, server_default="PRIVATE"))
    op.add_column("school", sa.Column("accent_color", sa.String(7), nullable=False, server_default="#185FA5"))

    op.create_unique_constraint("uq_school_subdomain", "school", ["subdomain"])
    op.create_unique_constraint("uq_school_custom_domain", "school", ["custom_domain"])
    op.create_unique_constraint("uq_school_emis_number", "school", ["emis_number"])
    op.create_unique_constraint("uq_school_waec_centre_number", "school", ["waec_centre_number"])

    op.create_index("ix_school_subdomain", "school", ["subdomain"])
    op.create_index("ix_school_custom_domain", "school", ["custom_domain"])


def downgrade() -> None:
    op.drop_index("ix_school_custom_domain", table_name="school")
    op.drop_index("ix_school_subdomain", table_name="school")

    op.drop_constraint("uq_school_waec_centre_number", "school", type_="unique")
    op.drop_constraint("uq_school_emis_number", "school", type_="unique")
    op.drop_constraint("uq_school_custom_domain", "school", type_="unique")
    op.drop_constraint("uq_school_subdomain", "school", type_="unique")

    op.drop_column("school", "accent_color")
    op.drop_column("school", "ownership_type")
    op.drop_column("school", "waec_centre_number")
    op.drop_column("school", "emis_number")
    op.drop_column("school", "custom_domain")
    op.drop_column("school", "subdomain")
