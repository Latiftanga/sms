"""Add HOUSEMASTER system position

Revision ID: 20250528_010
Revises: 20250528_009
Create Date: 2025-05-28
"""
from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20250528_010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.core.permissions import ALL_PERMISSIONS, POSITION_DEFAULTS

    pos_tbl = sa.table(
        "staff_position",
        sa.column("id", postgresql.UUID()),
        sa.column("school_id", postgresql.UUID()),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("is_system_template", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("created_by", postgresql.UUID()),
    )

    perm_tbl = sa.table(
        "position_permission",
        sa.column("position_id", postgresql.UUID()),
        sa.column("permission_key", sa.String),
        sa.column("granted", sa.Boolean),
    )

    pos_id = str(uuid.uuid4())
    op.bulk_insert(pos_tbl, [{
        "id": pos_id,
        "school_id": None,
        "name": "Housemaster",
        "code": "HOUSEMASTER",
        "is_system_template": True,
        "is_active": True,
        "created_by": None,
    }])

    granted_set = POSITION_DEFAULTS.get("HOUSEMASTER", {})
    perm_rows = [
        {
            "position_id": pos_id,
            "permission_key": perm_key,
            "granted": granted_set.get(perm_key, False),
        }
        for perm_key in ALL_PERMISSIONS
    ]
    op.bulk_insert(perm_tbl, perm_rows)


def downgrade() -> None:
    op.execute(
        "DELETE FROM staff_position WHERE code = 'HOUSEMASTER' AND is_system_template = TRUE"
    )
