"""Replace User.position_id (single role) with user_role junction table (M2M).

Migrates any existing position_id assignments into user_role rows before
dropping the old column.

Revision ID: 009
Revises: 008
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create user_role junction table ───────────────────────────────
    op.create_table(
        "user_role",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["staff_position.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_index("ix_user_role_user_id", "user_role", ["user_id"])

    # ── Migrate existing single-role assignments ───────────────────────
    op.execute("""
        INSERT INTO user_role (user_id, role_id, assigned_at)
        SELECT id, position_id, NOW()
        FROM "user"
        WHERE position_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)

    # ── Drop old single-role column ────────────────────────────────────
    op.drop_column("user", "position_id")


def downgrade() -> None:
    op.add_column("user",
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "user_position_id_fkey", "user", "staff_position",
        ["position_id"], ["id"], ondelete="SET NULL"
    )
    # Restore most-recent role as position_id (best-effort)
    op.execute("""
        UPDATE "user" u
        SET position_id = ur.role_id
        FROM (
            SELECT DISTINCT ON (user_id) user_id, role_id
            FROM user_role
            ORDER BY user_id, assigned_at DESC
        ) ur
        WHERE u.id = ur.user_id
    """)
    op.drop_index("ix_user_role_user_id", table_name="user_role")
    op.drop_table("user_role")
