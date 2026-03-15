"""ARQ worker and scheduler settings for the ETL pipeline.

WorkerSettings processes individual extraction jobs.
SchedulerSettings runs a cron tick every minute to evaluate which tenants
are due for extraction (3am local time).
"""

from arq import cron
from arq.connections import RedisSettings

from src.core.config import settings
from src.modules.analytics.workers.tasks import run_initial_load, run_tenant_extraction


class WorkerSettings:
    """ARQ worker that processes ETL extraction jobs."""

    functions = [run_tenant_extraction, run_initial_load]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    max_tries = 5
    job_timeout = 600  # 10 minutes per job

    @staticmethod
    async def on_startup(ctx):
        """Initialize DB session factory and Sentry for worker."""
        from src.core.database import SessionLocal

        import sentry_sdk

        if settings.SENTRY_DSN:
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                environment=settings.ENVIRONMENT,
                traces_sample_rate=0.1,
            )
        ctx["db_factory"] = SessionLocal

    @staticmethod
    async def on_shutdown(ctx):
        """Cleanup worker resources."""
        pass


class SchedulerSettings(WorkerSettings):
    """ARQ scheduler that ticks every minute to enqueue tenant extractions."""

    from src.modules.analytics.workers.scheduler import run_tick_scheduler

    cron_jobs = [
        cron(
            run_tick_scheduler,
            minute=set(range(60)),  # Every minute
        )
    ]
