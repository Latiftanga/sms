"""
ARQ background jobs.
Each function receives ctx as first argument (injected by ARQ).
ctx["session_factory"] is set in WorkerSettings.on_startup.
"""
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


# ── Smoke test ────────────────────────────────────────────────────

async def test_job(ctx: dict, message: str = "pong") -> str:
    """
    Phase 0 smoke test — verify worker is alive.
    Enqueue via: await arq_pool.enqueue_job("test_job", message="hello")
    """
    logger.info("test_job: %s", message)
    return f"worker received: {message}"


# ── Reports ───────────────────────────────────────────────────────

async def generate_report_card_pdf(
    ctx: dict,
    enrollment_id: str,
    term_id: str,
    school_id: str,
    generated_by_id: str,
) -> dict:
    """
    Generate a single student report card PDF.
    Saves to R2 and creates a DocumentRecord.
    Returns {"document_id": str, "storage_key": str}.
    """
    logger.info("Generating report card: enrollment=%s term=%s", enrollment_id, term_id)
    # TODO Phase 7: implement with WeasyPrint + Jinja2
    return {"document_id": None, "storage_key": None, "status": "not_implemented"}


async def bulk_generate_class_reports(
    ctx: dict,
    class_id: str,
    term_id: str,
    school_id: str,
    generated_by_id: str,
) -> dict:
    """
    Enqueue individual generate_report_card_pdf jobs for every student in a class.
    Returns job count.
    """
    logger.info("Bulk report generation: class=%s term=%s", class_id, term_id)
    # TODO Phase 7: query all active enrollments for the class+term, enqueue per student
    return {"enqueued": 0, "status": "not_implemented"}


# ── Communication ─────────────────────────────────────────────────

async def send_sms_notification(
    ctx: dict,
    phone_number: str,
    message: str,
    school_id: str,
) -> dict:
    """
    Send an SMS via Africa's Talking.
    Runs in background so API response is instant.
    """
    from app.core.config import settings

    if not settings.AT_API_KEY:
        logger.warning("Africa's Talking not configured — SMS skipped")
        return {"status": "skipped", "reason": "AT_API_KEY not set"}

    try:
        import africastalking  # type: ignore[import]
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        sms = africastalking.SMS
        response = sms.send(message, [phone_number], settings.AT_SENDER_ID)
        logger.info("SMS sent to %s: %s", phone_number, response)
        return {"status": "sent", "response": response}
    except Exception as exc:
        logger.error("SMS failed to %s: %s", phone_number, exc)
        return {"status": "failed", "error": str(exc)}


# ── Analytics ─────────────────────────────────────────────────────

async def refresh_analytics_views(ctx: dict) -> None:
    """
    Refresh materialized views for analytics dashboards.
    Scheduled via CronJob in WorkerSettings — runs every 6 hours.
    """
    logger.info("Refreshing analytics materialized views")
    session_factory = ctx.get("session_factory")
    if not session_factory:
        logger.error("No session_factory in ctx — worker startup may have failed")
        return

    async with session_factory() as session:
        from sqlalchemy import text
        # Materialized views will be created in Phase 10
        # op list kept here for future expansion
        views_to_refresh: list[str] = [
            # "mv_class_performance",
            # "mv_attendance_summary",
            # "mv_fee_collection",
        ]
        for view in views_to_refresh:
            try:
                await session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                logger.info("Refreshed %s", view)
            except Exception as exc:
                logger.error("Failed to refresh %s: %s", view, exc)
        await session.commit()
