"""Add missing indexes for FK columns and common query patterns.

PostgreSQL does NOT auto-index foreign key columns; every FK used in a
WHERE, JOIN, or ORDER BY clause needs an explicit index.

Also enables pg_trgm for efficient ILIKE search on name/ID columns.

Revision ID: 008
Revises: 007
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pg_trgm enables GIN indexes that make ILIKE/LIKE O(log n) instead of O(n)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── user ──────────────────────────────────────────────────────────
    # school_id: auth dep + per-school user queries
    op.create_index("ix_user_school_id", "user", ["school_id"])
    # staff_member_id: EXISTS subquery on staff detail, has_account batch check
    op.create_index("ix_user_staff_member_id", "user", ["staff_member_id"])

    # ── staff_member ──────────────────────────────────────────────────
    # school_id alone: used by every WHERE clause in staff endpoints
    op.create_index("ix_staff_member_school_id", "staff_member", ["school_id"])

    # Composite (school_id, last_name, first_name): covers the ORDER BY on the list
    # endpoint — the planner can use this for both filtering and sorting in one pass
    op.create_index(
        "ix_staff_member_school_name",
        "staff_member",
        ["school_id", "last_name", "first_name"],
    )

    # Partial index for active-only queries: far smaller than the full index,
    # planner prefers it when is_active = true filter is present
    op.execute(
        "CREATE INDEX ix_staff_member_school_active "
        "ON staff_member (school_id, last_name, first_name) "
        "WHERE is_active = true"
    )

    # Trigram GIN indexes for ILIKE search — first_name, last_name, id fields
    op.execute(
        "CREATE INDEX ix_staff_member_fname_trgm "
        "ON staff_member USING gin (first_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_staff_member_lname_trgm "
        "ON staff_member USING gin (last_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_staff_member_staff_id_trgm "
        "ON staff_member USING gin (staff_id gin_trgm_ops)"
    )

    # ── staff_promotion ───────────────────────────────────────────────
    # Composite with date_promoted: selectinload + ORDER BY date_promoted DESC
    op.create_index(
        "ix_staff_promotion_member_date",
        "staff_promotion",
        ["staff_member_id", "date_promoted"],
    )

    # ── staff_qualification ───────────────────────────────────────────
    op.create_index(
        "ix_staff_qualification_member",
        "staff_qualification",
        ["staff_member_id"],
    )

    # ── staff_permission ──────────────────────────────────────────────
    op.create_index(
        "ix_staff_permission_member",
        "staff_permission",
        ["staff_member_id"],
    )

    # ── staff_leave ───────────────────────────────────────────────────
    op.create_index("ix_staff_leave_member", "staff_leave", ["staff_member_id"])
    # Composite for date-range queries (upcoming / current leave)
    op.create_index(
        "ix_staff_leave_member_dates",
        "staff_leave",
        ["staff_member_id", "start_date", "end_date"],
    )

    # ── staff_position ────────────────────────────────────────────────
    # school_id: positions are always scoped to a school
    op.create_index("ix_staff_position_school_id", "staff_position", ["school_id"])


def downgrade() -> None:
    op.drop_index("ix_staff_position_school_id", table_name="staff_position")
    op.drop_index("ix_staff_leave_member_dates", table_name="staff_leave")
    op.drop_index("ix_staff_leave_member", table_name="staff_leave")
    op.drop_index("ix_staff_permission_member", table_name="staff_permission")
    op.drop_index("ix_staff_qualification_member", table_name="staff_qualification")
    op.drop_index("ix_staff_promotion_member_date", table_name="staff_promotion")
    op.execute("DROP INDEX IF EXISTS ix_staff_member_staff_id_trgm")
    op.execute("DROP INDEX IF EXISTS ix_staff_member_lname_trgm")
    op.execute("DROP INDEX IF EXISTS ix_staff_member_fname_trgm")
    op.execute("DROP INDEX IF EXISTS ix_staff_member_school_active")
    op.drop_index("ix_staff_member_school_name", table_name="staff_member")
    op.drop_index("ix_staff_member_school_id", table_name="staff_member")
    op.drop_index("ix_user_staff_member_id", table_name="user")
    op.drop_index("ix_user_school_id", table_name="user")
