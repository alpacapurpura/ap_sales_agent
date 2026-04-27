"""ARQ worker and scheduler settings for the ETL pipeline and CRM batch jobs.

WorkerSettings processes individual extraction jobs and CRM batch tasks.
SchedulerSettings runs cron jobs:
  - Every minute: evaluate which tenants are due for extraction (3am local time)
  - Daily at 4am UTC: inactivity detection and score decay
"""

from arq import cron
from arq.connections import RedisSettings

import src.shared.infrastructure.model_registry  # noqa: F401  — must be top-level for ARQ workers
from src.core.config import settings
from src.modules.analytics.workers.tasks import (
    run_campaign_sync,
    run_inactivity_detection,
    run_initial_load,
    run_mailerlite_etl_sync,
    run_period_extraction,
    run_tenant_extraction,
)
from src.modules.brand.workers.tasks import run_brand_extraction
from src.modules.copilot.application.services.event_cleanup import cleanup_old_events
from src.modules.copilot.observability.workers.aggregate_refresh_task import (
    refresh_daily_cost_mv,
)
from src.modules.copilot.observability.workers.cost_alert_task import (
    run_cost_alerts,
)
from src.modules.copilot.observability.workers.pricing_sync_task import sync_litellm_pricing
from src.modules.copilot.observability.workers.retention_task import (
    purge_expired_trace_rows,
)
from src.modules.offer.workers.tasks import run_offer_extraction
from src.modules.sales_agent.workers.frozen_detection import run_frozen_detection
from src.modules.tenant_domains.workers.tasks import poll_domain_verification
from src.shared.workers.brand_summary_regen import regen_brand_summary
from src.shared.workers.copilot_quality_eval import weekly_copilot_quality_eval
from src.shared.workers.copilot_rag_eval import weekly_copilot_rag_eval


class WorkerSettings:
    """ARQ worker that processes ETL extraction jobs and CRM batch tasks."""

    functions = [
        run_tenant_extraction,
        run_initial_load,
        run_period_extraction,
        run_inactivity_detection,
        run_mailerlite_etl_sync,
        run_campaign_sync,
        run_brand_extraction,
        run_offer_extraction,
        cleanup_old_events,
        poll_domain_verification,
        run_frozen_detection,
        regen_brand_summary,
        weekly_copilot_quality_eval,
        weekly_copilot_rag_eval,
        sync_litellm_pricing,
        refresh_daily_cost_mv,
        purge_expired_trace_rows,
        run_cost_alerts,
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    max_tries = 5
    job_timeout = 600  # 10 minutes per job

    @staticmethod
    async def on_startup(ctx: dict) -> None:
        """Initialize DB session factory, Redis, and Sentry for worker."""
        from src.core.database import SessionLocal, redis_client
        from src.core.sentry import init_sentry
        from src.modules.copilot.application.extraction_card_flow import (
            register_extraction_event_handlers,
        )
        from src.shared.application.brand_summary_event_handlers import (
            register_brand_summary_event_handlers,
        )

        init_sentry("worker")
        ctx["db_factory"] = SessionLocal
        ctx["redis_cache"] = redis_client
        register_extraction_event_handlers()
        register_brand_summary_event_handlers()

    @staticmethod
    async def on_shutdown(ctx: dict) -> None:
        """Cleanup worker resources."""


class SchedulerSettings:
    """ARQ scheduler with cron jobs for ETL and CRM batch processing.

    NOTE: arq's get_kwargs() uses __dict__ (not dir()), so inherited attributes
    are invisible. All settings must be defined directly on this class.
    """

    from src.modules.analytics.workers.scheduler import run_tick_scheduler

    # Repeat from WorkerSettings -- arq reads __dict__, not inherited attrs
    functions = [
        run_tenant_extraction,
        run_initial_load,
        run_period_extraction,
        run_inactivity_detection,
        run_mailerlite_etl_sync,
        run_campaign_sync,
        run_brand_extraction,
        run_offer_extraction,
        cleanup_old_events,
        poll_domain_verification,
        run_frozen_detection,
        regen_brand_summary,
        weekly_copilot_quality_eval,
        weekly_copilot_rag_eval,
        sync_litellm_pricing,
        refresh_daily_cost_mv,
        purge_expired_trace_rows,
        run_cost_alerts,
    ]
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
        cron(
            poll_domain_verification,
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},  # Every 5 minutes
        ),
        cron(
            run_frozen_detection,
            hour={0, 4, 8, 12, 16, 20},
            minute=30,  # Every 4 hours at :30
        ),
        # F9 — weekly LLM-judge eval over recent conversations.
        # Mondays 05:00 UTC keeps NANO calls bunched to a low-traffic
        # window. [COPILOT-LLM-JUDGE-F9]
        cron(
            weekly_copilot_quality_eval,
            weekday="mon",
            hour=5,
            minute=0,
        ),
        # F11.5 — weekly RAG retrieval eval over the curated marketing KB.
        # Mondays 06:00 UTC (1h after the quality eval to avoid stacking
        # NANO load). [COPILOT-RAG-EVAL-F11]
        cron(
            weekly_copilot_rag_eval,
            weekday="mon",
            hour=6,
            minute=0,
        ),
        # Phase 1 copilot observability rebuild — daily LiteLLM pricing
        # sync. 03:00 UTC keeps the run before the daily UTC report cuts
        # at 04:00 (inactivity_detection) so pricing is fresh for the day.
        cron(
            sync_litellm_pricing,
            hour=3,
            minute=0,
        ),
        # Phase 3 copilot observability rebuild — hourly daily-cost MV
        # refresh. CONCURRENT keeps the dashboard read path unblocked.
        # Minute 5 avoids stacking with on-the-hour ETL workers.
        cron(
            refresh_daily_cost_mv,
            minute=5,
        ),
        # Phase 3 copilot observability rebuild — daily retention purge.
        # 04:00 UTC after pricing_sync (03:00) so the trace_event table
        # is freshly aged before billing reports are pulled.
        cron(
            purge_expired_trace_rows,
            hour=4,
            minute=0,
        ),
        # Phase 3 copilot observability rebuild — daily cost-alert scan.
        # 12:00 UTC (≈07:00 PE/CO, 09:00 BR) so warnings land during
        # business hours.
        cron(
            run_cost_alerts,
            hour=12,
            minute=0,
        ),
    ]

    @staticmethod
    async def on_startup(ctx: dict) -> None:
        """Initialize DB session factory, Redis, and Sentry for scheduler."""
        from src.core.database import SessionLocal, redis_client
        from src.core.sentry import init_sentry
        from src.modules.copilot.application.extraction_card_flow import (
            register_extraction_event_handlers,
        )
        from src.shared.application.brand_summary_event_handlers import (
            register_brand_summary_event_handlers,
        )

        init_sentry("scheduler")
        ctx["db_factory"] = SessionLocal
        ctx["redis_cache"] = redis_client
        register_extraction_event_handlers()
        register_brand_summary_event_handlers()

    @staticmethod
    async def on_shutdown(ctx: dict) -> None:
        """Cleanup scheduler resources."""
