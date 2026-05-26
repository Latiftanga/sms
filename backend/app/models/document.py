import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class DocumentRecord(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Tracks generated documents (report cards, transcripts, certificates).
    verification_token is HMAC-SHA256 signed — verified by the public GET /verify/{token} endpoint.
    Revocation sets is_valid = False; the public endpoint returns a clear "REVOKED" response.
    """

    __tablename__ = "document_record"
    __table_args__ = (UniqueConstraint("verification_token"),)

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student.id", ondelete="CASCADE"), nullable=False
    )
    academic_term_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_term.id", ondelete="SET NULL"), nullable=True
    )
    # REPORT_CARD | TRANSCRIPT | CERTIFICATE | WAEC_FORM
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    verification_token: Mapped[str] = mapped_column(String(200), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)  # R2 object key
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # QR scan analytics
    scan_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_scanned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Revocation audit
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocation_reason: Mapped[str | None] = mapped_column(String(300))

    generated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )


class ImportBatch(UUIDPrimaryKey, TimestampMixin, Base):
    """
    Audit trail for every bulk import operation.
    Every imported record carries import_batch_id.
    """

    __tablename__ = "import_batch"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    # STUDENTS | STAFF | SCORES
    import_type: Mapped[str] = mapped_column(String(20), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clean_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # PREVIEW | COMMITTED | PARTIAL | FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PREVIEW")
    error_summary: Mapped[str | None] = mapped_column(String(2000))
    imported_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="RESTRICT"), nullable=False
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
