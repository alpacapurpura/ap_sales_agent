"""ARQ worker and scheduler settings for the ETL pipeline and CRM batch jobs.

WorkerSettings processes individual extraction jobs and CRM batch tasks.
SchedulerSettings runs cron jobs:
  - Every minute: evaluate which tenants are due for extraction (3am local time)
  - Daily at 4am UTC: inactivity detection and score decay
"""

from arq import cron
from arq.connections import RedisSettings

import src.shared.infrastructure.agent_observability_bootstrap
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
from src.modules.offer.workers.tasks import run_offer_extraction
from src.modules.sales_agent.observability.workers.dual_write_reconciliation_task import (
    run_sales_agent_dual_write_reconcile,
)
from src.modules.sales_agent.workers.appointment_reminder_engine import (
    run_appointment_reminders,
)
from src.modules.sales_agent.workers.frozen_detection import run_frozen_detection
from src.modules.sales_agent.workers.payment_reminder_engine import (
    run_payment_reminder_engine,
)
from src.modules.sales_agent.workers.verify_pending_bookings import (
    run_verify_pending_bookings,
)
from src.modules.sales_agent.workers.verify_pending_payments import (
    run_verify_pending_payments,
)
from src.modules.tenant_domains.workers.tasks import poll_domain_verification
from src.shared.agent_observability.workers.aggregate_refresh_task import (
    refresh_daily_cost_mv,
)
from src.shared.agent_observability.workers.cost_alert_task import run_cost_alerts
from src.shared.agent_observability.workers.pricing_sync_task import sync_litellm_pricing
from src.shared.agent_observability.workers.retention_task import purge_expired_trace_rows
from src.shared.workers.brand_summary_regen import regen_brand_summary
from src.shared.workers.copilot_quality_eval import weekly_copilot_quality_eval
from src.shared.workers.copilot_rag_eval import weekly_copilot_rag_eval
from src.shared.workers.sales_agent_quality_eval import weekly_sales_agent_quality_eval


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
        weekly_sales_agent_quality_eval,
        sync_litellm_pricing,
        refresh_daily_cost_mv,
        purge_expired_trace_rows,
        run_cost_alerts,
        run_sales_agent_dual_write_reconcile,
        run_verify_pending_bookings,
        run_appointment_reminders,
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

        # S8 — bridge AppointmentEvent / BookingMissedEvent into
        # scheduled_meetings JSONB. Idempotent registration.
        from src.modules.sales_agent.application.scheduling_event_handlers import (
            register_scheduling_event_handlers,
        )

        register_scheduling_event_handlers()

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
        weekly_sales_agent_quality_eval,
        sync_litellm_pricing,
        refresh_daily_cost_mv,
        purge_expired_trace_rows,
        run_cost_alerts,
        run_sales_agent_dual_write_reconcile,
        run_verify_pending_bookings,
        run_appointment_reminders,
        run_verify_pending_payments,
        run_payment_reminder_engine,
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
        # S10 — weekly sales_agent quality eval over canonical goldens.
        # Mondays 07:00 UTC (1h after RAG to avoid stacking NANO load).
        # Stub default; opt-in real LLM via ``RUN_LLM_JUDGE=1``.
        cron(
            weekly_sales_agent_quality_eval,
            weekday="mon",
            hour=7,
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
        # Sales-agent S1 dual-write reconciliation — hourly when opt-in
        # via ``SALES_AGENT_DUAL_WRITE_RECONCILE=1``. Minute 25 avoids
        # stacking with the on-the-hour ETL + on-:05 cost MV refresh.
        # Off by default; turn on for the ~4-week dual-write window
        # then leave disabled (S6 cutover removes the legacy table read).
        cron(
            run_sales_agent_dual_write_reconcile,
            minute=25,
        ),
        # S8 — verify pending bookings (link expiry + missed inference).
        # Every 15 min on :07 / :22 / :37 / :52 to avoid colliding with
        # ETL on-the-hour and cost MV on-:05.
        cron(
            run_verify_pending_bookings,
            minute={7, 22, 37, 52},
        ),
        # S8 — appointment reminder engine (T-24h / T-1h / T+1h postcheck).
        # Same cadence as verify_pending_bookings but offset by 5 minutes
        # so the verify cron lands first and entries are fresh.
        cron(
            run_appointment_reminders,
            minute={12, 27, 42, 57},
        ),
        # S9 — verify pending payments (pull reconciler for payment links).
        # Every 15 min on :09 / :24 / :39 / :54 to offset from bookings verify.
        cron(
            run_verify_pending_payments,
            minute={9, 24, 39, 54},
        ),
        # S9 — payment reminder engine (T+2h nudge for unpaid links).
        # Every 30 min on :15 / :45.
        cron(
            run_payment_reminder_engine,
            minute={15, 45},
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

        # S8 — bridge AppointmentEvent / BookingMissedEvent into
        # scheduled_meetings JSONB. Idempotent registration.
        from src.modules.sales_agent.application.scheduling_event_handlers import (
            register_scheduling_event_handlers,
        )

        register_scheduling_event_handlers()

    @staticmethod
    async def on_shutdown(ctx: dict) -> None:
        """Cleanup scheduler resources."""
