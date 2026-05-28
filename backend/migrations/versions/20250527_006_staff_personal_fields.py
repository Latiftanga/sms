"""Add personal fields to staff_member, letter_reference to staff_promotion, must_change_password to user

Revision ID: 20250527_006
Revises: 005
Create Date: 2025-05-27
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # staff_member personal & contact fields
    op.add_column("staff_member", sa.Column("staff_id", sa.String(30), nullable=True))
    op.add_column("staff_member", sa.Column("gender", sa.String(10), nullable=True))
    op.add_column("staff_member", sa.Column("date_of_birth", sa.Date, nullable=True))
    op.add_column("staff_member", sa.Column("phone", sa.String(20), nullable=True))
    op.add_column("staff_member", sa.Column("personal_email", sa.String(254), nullable=True))
    op.add_column("staff_member", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("staff_member", sa.Column("emergency_contact_name", sa.String(160), nullable=True))
    op.add_column("staff_member", sa.Column("emergency_contact_phone", sa.String(20), nullable=True))
    op.create_index("ix_staff_member_staff_id", "staff_member", ["staff_id"])

    # staff_promotion — GES letter reference
    op.add_column("staff_promotion", sa.Column("letter_reference", sa.String(80), nullable=True))

    # user — force password change on first login
    op.add_column("user", sa.Column("must_change_password", sa.Boolean, nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("user", "must_change_password")
    op.drop_column("staff_promotion", "letter_reference")
    op.drop_index("ix_staff_member_staff_id", table_name="staff_member")
    op.drop_column("staff_member", "emergency_contact_phone")
    op.drop_column("staff_member", "emergency_contact_name")
    op.drop_column("staff_member", "address")
    op.drop_column("staff_member", "personal_email")
    op.drop_column("staff_member", "phone")
    op.drop_column("staff_member", "date_of_birth")
    op.drop_column("staff_member", "gender")
    op.drop_column("staff_member", "staff_id")
