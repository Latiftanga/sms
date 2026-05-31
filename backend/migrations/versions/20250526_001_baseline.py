"""Baseline schema — all tables + seed data

Revision ID: 001
Revises:
Create Date: 2025-05-26
"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _create_extensions()
    _create_tables()
    _create_indexes()
    _seed_ghana_holidays()
    _seed_grading_scales()
    _seed_staff_positions()


def downgrade() -> None:
    # Drop in reverse dependency order
    tables = [
        "import_batch", "document_record",
        "fee_payment", "fee_structure",
        "score", "student_subject_registration",
        "attendance_record",
        "student_behaviour_record", "student_term_enrollment",
        "student_class_enrollment", "guardian", "student",
        "subject_teacher", "class_teacher", "class_subject", "class",
        "house", "school_period", "school_calendar",
        "academic_term", "academic_year",
        "staff_leave", "staff_qualification", "staff_promotion",
        "staff_permission", "staff_member",
        '"user"',
        "position_permission", "staff_position",
        "school_config", "school_schedule", "school",
        "grade", "grading_scale",
        "ghana_public_holiday",
    ]
    for t in tables:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {t} CASCADE"))


# ─────────────────────────────────────────────────────────────────────────────
# DDL helpers
# ─────────────────────────────────────────────────────────────────────────────

def _create_extensions() -> None:
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))


def _create_tables() -> None:
    # ── Reference ────────────────────────────────────────────────────────────
    op.create_table(
        "ghana_public_holiday",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("month", sa.Integer, nullable=True),
        sa.Column("day", sa.Integer, nullable=True),
        sa.Column("holiday_type", sa.String(30), nullable=False, server_default="FIXED"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    # ── School (must precede grading_scale which FKs to it) ─────────────────
    op.create_table(
        "school",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("slug", sa.String(220), nullable=False, unique=True),
        sa.Column("country", sa.String(60), nullable=False, server_default="Ghana"),
        sa.Column("region", sa.String(80), nullable=True),
        sa.Column("district", sa.String(80), nullable=True),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("education_levels", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("facility_type", sa.String(20), nullable=False, server_default="MIXED"),
        sa.Column("has_houses", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("has_fees_module", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Grading ──────────────────────────────────────────────────────────────
    op.create_table(
        "grading_scale",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("education_levels", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_observational", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "grade",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("grading_scale_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("grading_scale.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(10), nullable=False),
        sa.Column("min_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("remark", sa.String(60), nullable=True),
        sa.Column("points", sa.Numeric(4, 1), nullable=True),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("is_pass", sa.Boolean, nullable=False, server_default="true"),
        sa.UniqueConstraint("grading_scale_id", "label"),
    )

    op.create_table(
        "school_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("grading_scale_id_basic", postgresql.UUID(as_uuid=True), sa.ForeignKey("grading_scale.id"), nullable=True),
        sa.Column("grading_scale_id_shs", postgresql.UUID(as_uuid=True), sa.ForeignKey("grading_scale.id"), nullable=True),
        sa.Column("grading_scale_id_early", postgresql.UUID(as_uuid=True), sa.ForeignKey("grading_scale.id"), nullable=True),
        sa.Column("report_template_basic", sa.String(100), nullable=True),
        sa.Column("report_template_shs", sa.String(100), nullable=True),
        sa.Column("report_template_early", sa.String(100), nullable=True),
        sa.Column("register_number_pattern", sa.String(100), nullable=False, server_default="{code}/{year}/{seq:04d}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "school_schedule",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("school_days", postgresql.ARRAY(sa.Integer), nullable=False, server_default="{1,2,3,4,5}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Staff positions & permissions ────────────────────────────────────────
    op.create_table(
        "staff_position",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("is_system_template", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("school_id", "code"),
    )

    op.create_table(
        "position_permission",
        sa.Column("position_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_position.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_key", sa.String(60), primary_key=True),
        sa.Column("granted", sa.Boolean, nullable=False, server_default="true"),
        sa.UniqueConstraint("position_id", "permission_key"),
    )

    # ── Users ────────────────────────────────────────────────────────────────
    op.create_table(
        "user",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("system_role", sa.String(20), nullable=False, server_default="SCHOOL_STAFF"),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="SET NULL"), nullable=True),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_position.id", ondelete="SET NULL"), nullable=True),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invite_token", sa.String(100), nullable=True, unique=True),
        sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Staff members ────────────────────────────────────────────────────────
    op.create_table(
        "staff_member",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("middle_name", sa.String(80), nullable=True),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("employment_type", sa.String(20), nullable=False, server_default="PERMANENT"),
        sa.Column("designation", sa.String(120), nullable=True),
        sa.Column("date_joined", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("ges_staff_id", sa.String(30), nullable=True),
        sa.Column("registered_no", sa.String(30), nullable=True),
        sa.Column("licence_no", sa.String(30), nullable=True),
        sa.Column("ssnit", sa.String(30), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "staff_permission",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_key", sa.String(60), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("staff_member_id", "school_id", "permission_key"),
    )

    op.create_table(
        "staff_promotion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.String(120), nullable=False),
        sa.Column("date_obtained", sa.Date, nullable=False),
        sa.Column("date_recorded", sa.Date, nullable=False),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "staff_qualification",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("degree", sa.String(150), nullable=False),
        sa.Column("institution", sa.String(200), nullable=False),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "staff_leave",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type", sa.String(30), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Academic ──────────────────────────────────────────────────────────────
    op.create_table(
        "academic_year",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "academic_term",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("education_levels", postgresql.ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("block_owing_students", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("block_owing_students_set_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("block_owing_students_set_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "school_calendar",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_term_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_term.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("day_type", sa.String(20), nullable=False),
        sa.Column("label", sa.String(120), nullable=True),
        sa.Column("is_auto_generated", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("school_id", "academic_term_id", "date"),
    )

    op.create_table(
        "school_period",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("is_lesson", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("school_id", "position"),
    )

    op.create_table(
        "house",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("housemaster_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "class",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("year_group", sa.String(20), nullable=False),
        sa.Column("stream", sa.String(40), nullable=True),
        sa.Column("education_level", sa.String(30), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "class_subject",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("class.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_name", sa.String(100), nullable=False),
        sa.Column("subject_code", sa.String(20), nullable=False),
        sa.Column("is_core", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("class_id", "subject_code"),
    )

    op.create_table(
        "class_teacher",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("class.id", ondelete="CASCADE"), nullable=False),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_member.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("class_id", "academic_year_id"),
    )

    op.create_table(
        "subject_teacher",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("class_subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("class_subject.id", ondelete="CASCADE"), nullable=False),
        sa.Column("staff_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("staff_member.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("class_subject_id", "staff_member_id", "academic_year_id"),
    )

    # ── Students ──────────────────────────────────────────────────────────────
    op.create_table(
        "student",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("middle_name", sa.String(80), nullable=True),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("place_of_birth", sa.String(150), nullable=True),
        sa.Column("nationality", sa.String(60), nullable=False, server_default="Ghanaian"),
        sa.Column("religion", sa.String(60), nullable=True),
        sa.Column("school_issued_id", sa.String(50), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("admission_date", sa.Date, nullable=True),
        sa.Column("admission_number", sa.String(50), nullable=True),
        sa.Column("previous_school", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "guardian",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("relationship_type", sa.String(30), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("is_primary_contact", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "import_batch",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("import_type", sa.String(20), nullable=False),
        sa.Column("total_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clean_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_rows", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PREVIEW"),
        sa.Column("error_summary", sa.String(2000), nullable=True),
        sa.Column("imported_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "student_class_enrollment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("class.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_year.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("house_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("house.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_type", sa.String(10), nullable=False, server_default="DAY"),
        sa.Column("register_number", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("left_date", sa.Date, nullable=True),
        sa.Column("left_reason", sa.Text, nullable=True),
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batch.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("student_id", "academic_year_id"),
    )

    op.create_table(
        "student_term_enrollment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_class_enrollment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_class_enrollment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_term_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_term.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("enrolled_date", sa.Date, nullable=False),
        sa.Column("fee_status", sa.String(20), nullable=False, server_default="NOT_APPLICABLE"),
        sa.Column("fee_cleared_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fee_cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("waiver_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("student_class_enrollment_id", "academic_term_id"),
    )

    op.create_table(
        "student_behaviour_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_term_enrollment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_term_enrollment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("conduct", sa.String(20), nullable=True),
        sa.Column("attitude", sa.String(20), nullable=True),
        sa.Column("punctuality", sa.String(20), nullable=True),
        sa.Column("interest", sa.String(20), nullable=True),
        sa.Column("class_teacher_remark", sa.Text, nullable=True),
        sa.Column("head_teacher_remark", sa.Text, nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Attendance ────────────────────────────────────────────────────────────
    op.create_table(
        "attendance_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_term_enrollment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_term_enrollment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_calendar_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school_calendar.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("school_period_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school_period.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("marked_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("marked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("student_term_enrollment_id", "school_calendar_id", "school_period_id"),
    )

    # ── Assessment ────────────────────────────────────────────────────────────
    op.create_table(
        "student_subject_registration",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_term_enrollment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_term_enrollment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("class_subject.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("student_term_enrollment_id", "class_subject_id"),
    )

    op.create_table(
        "score",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_subject_registration_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_subject_registration.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assessment_type", sa.String(20), nullable=False),
        sa.Column("assessment_label", sa.String(80), nullable=True),
        sa.Column("raw_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("max_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("entered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("score.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("is_approved", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("import_batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_batch.id", ondelete="SET NULL"), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Fees ──────────────────────────────────────────────────────────────────
    op.create_table(
        "fee_structure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_year.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_term_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_term.id", ondelete="CASCADE"), nullable=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("class.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_type", sa.String(10), nullable=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="GHS"),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "fee_payment",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("student_class_enrollment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student_class_enrollment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_term_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("academic_term.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fee_structure_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fee_structure.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("amount_paid", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="GHS"),
        sa.Column("payment_method", sa.String(20), nullable=False),
        sa.Column("receipt_number", sa.String(50), nullable=False, unique=True),
        sa.Column("payment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "document_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("school.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("student.id", ondelete="CASCADE"), nullable=False),
        sa.Column("academic_term_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("verification_token", sa.String(200), nullable=False, unique=True),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("is_valid", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("scan_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(300), nullable=True),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def _create_indexes() -> None:
    op.create_index("ix_student_school", "student", ["school_id"])
    op.create_index("ix_student_issued_id", "student", ["school_id", "school_issued_id"])
    op.create_index("ix_staff_school", "staff_member", ["school_id"])
    op.create_index("ix_staff_ges_id", "staff_member", ["ges_staff_id"])
    op.create_index("ix_calendar_school_term", "school_calendar", ["school_id", "academic_term_id"])
    op.create_index("ix_calendar_date", "school_calendar", ["date"])
    op.create_index("ix_attendance_enrollment", "attendance_record", ["student_term_enrollment_id"])
    op.create_index("ix_attendance_calendar", "attendance_record", ["school_calendar_id"])
    op.create_index("ix_score_registration", "score", ["student_subject_registration_id"])
    op.create_index("ix_user_email", "user", ["email"])
    op.create_index("ix_enrollment_register", "student_class_enrollment", ["register_number"])
    op.create_index("ix_fee_payment_enrollment", "fee_payment", ["student_class_enrollment_id"])


# ─────────────────────────────────────────────────────────────────────────────
# Seed data
# ─────────────────────────────────────────────────────────────────────────────

def _seed_ghana_holidays() -> None:
    holidays = [
        {"name": "New Year's Day",     "month": 1,    "day": 1,    "holiday_type": "FIXED"},
        {"name": "Constitution Day",   "month": 1,    "day": 7,    "holiday_type": "FIXED"},
        {"name": "Independence Day",   "month": 3,    "day": 6,    "holiday_type": "FIXED"},
        {"name": "Good Friday",        "month": None, "day": None, "holiday_type": "EASTER_GOOD_FRIDAY"},
        {"name": "Easter Monday",      "month": None, "day": None, "holiday_type": "EASTER_MONDAY"},
        {"name": "May Day",            "month": 5,    "day": 1,    "holiday_type": "FIXED"},
        {"name": "Africa Union Day",   "month": 5,    "day": 25,   "holiday_type": "FIXED"},
        {"name": "Republic Day",       "month": 7,    "day": 1,    "holiday_type": "FIXED"},
        {"name": "Founders Day",       "month": 8,    "day": 4,    "holiday_type": "FIXED"},
        {"name": "Kwame Nkrumah Day",  "month": 9,    "day": 21,   "holiday_type": "FIXED"},
        {"name": "Farmers Day",        "month": None, "day": None, "holiday_type": "FARMERS_DAY"},
        {"name": "Christmas Day",      "month": 12,   "day": 25,   "holiday_type": "FIXED"},
        {"name": "Boxing Day",         "month": 12,   "day": 26,   "holiday_type": "FIXED"},
    ]
    op.bulk_insert(
        sa.table(
            "ghana_public_holiday",
            sa.column("id", postgresql.UUID()),
            sa.column("name", sa.String),
            sa.column("month", sa.Integer),
            sa.column("day", sa.Integer),
            sa.column("holiday_type", sa.String),
            sa.column("is_active", sa.Boolean),
        ),
        [{"id": str(uuid.uuid4()), "is_active": True, **h} for h in holidays],
    )


def _seed_grading_scales() -> None:
    bece_id = str(uuid.uuid4())
    wassce_id = str(uuid.uuid4())
    ecm_id = str(uuid.uuid4())

    scales_tbl = sa.table(
        "grading_scale",
        sa.column("id", postgresql.UUID()),
        sa.column("school_id", postgresql.UUID()),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("education_levels", postgresql.ARRAY(sa.String)),
        sa.column("is_default", sa.Boolean),
        sa.column("is_observational", sa.Boolean),
    )
    op.bulk_insert(scales_tbl, [
        {"id": bece_id,   "school_id": None, "name": "WAEC BECE",                 "code": "BECE",   "education_levels": ["BASIC", "JHS"],  "is_default": True, "is_observational": False},
        {"id": wassce_id, "school_id": None, "name": "WASSCE",                    "code": "WASSCE", "education_levels": ["SHS"],            "is_default": True, "is_observational": False},
        {"id": ecm_id,    "school_id": None, "name": "Early Childhood Milestones","code": "ECM",    "education_levels": ["EARLY_CHILDHOOD"],"is_default": True, "is_observational": True},
    ])

    grades_tbl = sa.table(
        "grade",
        sa.column("id", postgresql.UUID()),
        sa.column("grading_scale_id", postgresql.UUID()),
        sa.column("label", sa.String),
        sa.column("min_score", sa.Numeric),
        sa.column("max_score", sa.Numeric),
        sa.column("remark", sa.String),
        sa.column("points", sa.Numeric),
        sa.column("position", sa.Integer),
        sa.column("is_pass", sa.Boolean),
    )

    bece_grades = [
        {"label": "1", "min_score": 80,    "max_score": 100,   "remark": "Excellent",  "points": None, "position": 1, "is_pass": True},
        {"label": "2", "min_score": 70,    "max_score": 79.99, "remark": "Very Good",  "points": None, "position": 2, "is_pass": True},
        {"label": "3", "min_score": 60,    "max_score": 69.99, "remark": "Good",       "points": None, "position": 3, "is_pass": True},
        {"label": "4", "min_score": 50,    "max_score": 59.99, "remark": "Credit",     "points": None, "position": 4, "is_pass": True},
        {"label": "5", "min_score": 40,    "max_score": 49.99, "remark": "Pass",       "points": None, "position": 5, "is_pass": True},
        {"label": "6", "min_score": 30,    "max_score": 39.99, "remark": "Pass",       "points": None, "position": 6, "is_pass": True},
        {"label": "7", "min_score": 20,    "max_score": 29.99, "remark": "Weak Pass",  "points": None, "position": 7, "is_pass": False},
        {"label": "8", "min_score": 0,     "max_score": 19.99, "remark": "Fail",       "points": None, "position": 8, "is_pass": False},
    ]

    wassce_grades = [
        {"label": "A1", "min_score": 80,    "max_score": 100,   "remark": "Excellent", "points": 1.0, "position": 1, "is_pass": True},
        {"label": "B2", "min_score": 75,    "max_score": 79.99, "remark": "Very Good", "points": 2.0, "position": 2, "is_pass": True},
        {"label": "B3", "min_score": 70,    "max_score": 74.99, "remark": "Good",      "points": 3.0, "position": 3, "is_pass": True},
        {"label": "C4", "min_score": 65,    "max_score": 69.99, "remark": "Credit",    "points": 4.0, "position": 4, "is_pass": True},
        {"label": "C5", "min_score": 60,    "max_score": 64.99, "remark": "Credit",    "points": 5.0, "position": 5, "is_pass": True},
        {"label": "C6", "min_score": 55,    "max_score": 59.99, "remark": "Credit",    "points": 6.0, "position": 6, "is_pass": True},
        {"label": "D7", "min_score": 50,    "max_score": 54.99, "remark": "Pass",      "points": 7.0, "position": 7, "is_pass": False},
        {"label": "E8", "min_score": 45,    "max_score": 49.99, "remark": "Weak Pass", "points": 8.0, "position": 8, "is_pass": False},
        {"label": "F9", "min_score": 0,     "max_score": 44.99, "remark": "Fail",      "points": 9.0, "position": 9, "is_pass": False},
    ]

    ecm_grades = [
        {"label": "4", "min_score": None, "max_score": None, "remark": "Exceeds Expectations",    "points": None, "position": 1, "is_pass": True},
        {"label": "3", "min_score": None, "max_score": None, "remark": "Meets Expectations",      "points": None, "position": 2, "is_pass": True},
        {"label": "2", "min_score": None, "max_score": None, "remark": "Approaching Expectations","points": None, "position": 3, "is_pass": True},
        {"label": "1", "min_score": None, "max_score": None, "remark": "Needs Support",           "points": None, "position": 4, "is_pass": False},
    ]

    all_grades = (
        [{"id": str(uuid.uuid4()), "grading_scale_id": bece_id,   **g} for g in bece_grades] +
        [{"id": str(uuid.uuid4()), "grading_scale_id": wassce_id, **g} for g in wassce_grades] +
        [{"id": str(uuid.uuid4()), "grading_scale_id": ecm_id,    **g} for g in ecm_grades]
    )
    op.bulk_insert(grades_tbl, all_grades)


def _seed_staff_positions() -> None:
    from app.core.permissions import POSITION_DEFAULTS, ALL_PERMISSIONS

    positions = [
        {"code": "ADMIN",             "name": "Admin"},
        {"code": "HEADTEACHER",       "name": "Headteacher"},
        {"code": "ASSISTANT_HEAD",    "name": "Assistant Headteacher"},
        {"code": "SENIOR_HOUSEMASTER","name": "Senior Housemaster"},
        {"code": "BURSAR",            "name": "Bursar"},
        {"code": "CLASS_TEACHER",     "name": "Class Teacher"},
    ]

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

    perm_rows: list[dict] = []
    for pos in positions:
        pos_id = str(uuid.uuid4())
        op.bulk_insert(pos_tbl, [{
            "id": pos_id,
            "school_id": None,
            "name": pos["name"],
            "code": pos["code"],
            "is_system_template": True,
            "is_active": True,
            "created_by": None,
        }])
        granted_set = POSITION_DEFAULTS.get(pos["code"], {})
        for perm_key in ALL_PERMISSIONS:
            perm_rows.append({
                "position_id": pos_id,
                "permission_key": perm_key,
                "granted": granted_set.get(perm_key, False),
            })

    op.bulk_insert(perm_tbl, perm_rows)
