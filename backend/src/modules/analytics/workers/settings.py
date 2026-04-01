"""ARQ worker and scheduler settings for the ETL pipeline and CRM batch jobs.

WorkerSettings processes individual extraction jobs and CRM batch tasks.
SchedulerSettings runs cron jobs:
  - Every minute: evaluate which tenants are due for extraction (3am local time)
  - Daily at 4am UTC: inactivity detection and score decay
"""

from arq import cron
from arq.connections import RedisSettings

from src.core.config import settings
import src.shared.infrastructure.model_registry  # noqa: F401  — must be top-level for ARQ workers
from src.modules.analytics.workers.tasks import (
    run_initial_load,
    run_inactivity_detection,
    run_mailerlite_etl_sync,
    run_tenant_extraction,
)
from src.modules.brand.workers.tasks import run_brand_extraction
from src.modules.copilot.application.services.event_cleanup import cleanup_old_events


class WorkerSettings:
    """ARQ worker that processes ETL extraction jobs and CRM batch tasks."""

    functions = [run_tenant_extraction, run_initial_load, run_inactivity_detection, run_mailerlite_etl_sync, run_brand_extraction, cleanup_old_events]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    max_tries = 5
    job_timeout = 600  # 10 minutes per job

    @staticmethod
    async def on_startup(ctx):
        """Initialize DB session factory, Redis, and Sentry for worker."""
        from src.core.database import SessionLocal, redis_client
        from src.core.sentry import init_sentry

        init_sentry("worker")
        ctx["db_factory"] = SessionLocal
        ctx["redis_cache"] = redis_client

    @staticmethod
    async def on_shutdown(ctx):
        """Cleanup worker resources."""
        pass


class SchedulerSettings:
    """ARQ scheduler with cron jobs for ETL and CRM batch processing.

    NOTE: arq's get_kwargs() uses __dict__ (not dir()), so inherited attributes
    are invisible. All settings must be defined directly on this class.
    """

    from src.modules.analytics.workers.scheduler import run_tick_scheduler

    # Repeat from WorkerSettings -- arq reads __dict__, not inherited attrs
    functions = [run_tenant_extraction, run_initial_load, run_inactivity_detection, run_mailerlite_etl_sync, run_brand_extraction, cleanup_old_events]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    max_tries = 5
    job_timeout = 600

    cron_jobs = [
        cron(
            run_tick_scheduler,
            minute=set(range(60)),  # Every minute
        ),
        cron(
            run_inactivity_detection,
            hour=4,
            minute=0,  # Daily at 4am UTC
        ),
        cron(
            run_mailerlite_etl_sync,
            hour={0, 6, 12, 18},
            minute=15,  # Every 6 hours at :15
        ),
        cron(
            cleanup_old_events,
            hour=3,
            minute=30,  # Daily at 3:30am UTC
        ),
    ]

    @staticmethod
    async def on_startup(ctx):
        """Initialize DB session factory, Redis, and Sentry for scheduler."""
        from src.core.database import SessionLocal, redis_client
        from src.core.sentry import init_sentry

        init_sentry("scheduler")
        ctx["db_factory"] = SessionLocal
        ctx["redis_cache"] = redis_client

    @staticmethod
    async def on_shutdown(ctx):
        """Cleanup scheduler resources."""
        pass
