from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.workers import jobs


async def startup(ctx: dict) -> None:
    from app.core.redis import init_redis
    from app.core.db import AsyncSessionLocal
    await init_redis()
    ctx["session_factory"] = AsyncSessionLocal


async def shutdown(ctx: dict) -> None:
    from app.core.redis import close_redis
    await close_redis()


class WorkerSettings:
    functions = [
        jobs.test_job,
        jobs.generate_report_card_pdf,
        jobs.bulk_generate_class_reports,
        jobs.send_sms_notification,
    ]
    cron_jobs = [
        # Refresh materialized analytics views every 6 hours
        cron(jobs.refresh_analytics_views, hour={0, 6, 12, 18}, minute=0),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    queue_name = "ttek_sis"
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per job
    keep_result = 3600  # keep results for 1 hour
