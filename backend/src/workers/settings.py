"""ARQ worker and scheduler settings for the ETL pipeline and CRM batch jobs.

WorkerSettings processes individual extraction jobs and CRM batch tasks.
SchedulerSettings runs cron jobs:
  - Every minute: evaluate which tenants are due for extraction (3am local time)
  - Daily at 4am UTC: inactivity detection and score decay
"""

from arq import cron
from arq.connections import RedisSettings
from luana_core_analytics_engine.workers.tasks import (
    run_campaign_sync,
    run_inactivity_detection,
    run_initial_load,
    run_mailerlite_etl_sync,
    run_period_extraction,
    run_tenant_extraction,
)
from luana_core_brand_studio.workers.tasks import run_brand_extraction

# PI-1 S2 PR-5 — campaigns ARQ workers
from luana_core_campaigns.workers.audit_retention_task import purge_old_campaigns_audit
from luana_core_campaigns.workers.execution_task import run_campaign_execution_task
from luana_core_campaigns.workers.scheduler_tick import run_campaign_scheduler_tick
from luana_core_campaigns.workers.segment_refresh_tick import run_segment_refresh_tick
from luana_core_copilot.application.services.event_cleanup import cleanup_old_events
from luana_core_copilot.infrastructure.workers.telegram_worker import (
    process_copilot_telegram_turn,
)
from luana_core_observability.workers.aggregate_refresh_task import (
    refresh_daily_cost_mv,
)
from luana_core_observability.workers.cost_alert_task import run_cost_alerts
from luana_core_observability.workers.pricing_sync_task import sync_litellm_pricing
from luana_core_observability.workers.retention_task import purge_expired_trace_rows
from luana_core_offer_studio.workers.tasks import run_offer_extraction
from luana_core_platform.core.config import settings
from luana_core_platform.workers.brand_summary_regen import regen_brand_summary
from luana_core_sales_agent.observability.workers.dual_write_reconciliation_task import (
    run_sales_agent_dual_write_reconcile,
)
from luana_core_sales_agent.workers.appointment_reminder_engine import (
    run_appointment_reminders,
)
from luana_core_sales_agent.workers.frozen_detection import run_frozen_detection
from luana_core_sales_agent.workers.payment_reminder_engine import (
    run_payment_reminder_engine,
)
from luana_core_sales_agent.workers.verify_pending_bookings import (
    run_verify_pending_bookings,
)
from luana_core_sales_agent.workers.verify_pending_payments import (
    run_verify_pending_payments,
)
from luana_core_tenant_domains.workers.tasks import poll_domain_verification

import src.shared.infrastructure.agent_observability_bootstrap
import src.shared.infrastructure.model_registry  # noqa: F401  — must be top-level for ARQ workers
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
        # PI-1 S2 PR-5 campaigns workers
        run_campaign_execution_task,
        run_campaign_scheduler_tick,
        run_segment_refresh_tick,
        purge_old_campaigns_audit,
        # PI-5 PR-1 — Copilot Telegram channel
        process_copilot_telegram_turn,
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    max_tries = 5
    job_timeout = 600  # 10 minutes per job

    @staticmethod
    async def on_startup(ctx: dict) -> None:
        """Initialize DB session factory, Redis, and Sentry for worker."""
        from luana_core_copilot.application.extraction_card_flow import (
            register_extraction_event_handlers,
        )
        from luana_core_observability.recording.cost_recorder import (
            register_cost_recorder,
        )
        from luana_core_platform.application.brand_summary_event_handlers import (
            register_brand_summary_event_handlers,
        )
        from luana_core_platform.core.database import SessionLocal, redis_client
        from luana_core_platform.core.sentry import init_sentry

        init_sentry("worker")
        ctx["db_factory"] = SessionLocal
        ctx["redis_cache"] = redis_client
        register_extraction_event_handlers()
        register_brand_summary_event_handlers()

        # PI-12 S1 T-1 — process-wide LiteLLM CustomLogger for cost capture.
        # Workers run extraction orchestrators that invoke LLMs; the recorder
        # MUST be registered here too (process-isolated from FastAPI).
        register_cost_recorder()

        # S8 — bridge AppointmentEvent / BookingMissedEvent into
        # scheduled_meetings JSONB. Idempotent registration.
        from luana_core_sales_agent.application.scheduling_event_handlers import (
            register_scheduling_event_handlers,
        )

        register_scheduling_event_handlers()

        # PI-1 S2 PR-5 — campaigns channel registry bootstrap.
        # token_provider: env TELEGRAM_BOT_TOKEN global fallback (dev-app smoke).
        # Tenant-specific tokens wired in S3+ via connections module.
        from luana_core_campaigns.infrastructure.channels.registry import (
            register_default_channels,
        )

        async def _env_telegram_token_provider(_tenant_id: object) -> str:
            import os

            return os.environ.get("TELEGRAM_BOT_TOKEN", "")

        register_default_channels(telegram_token_provider=_env_telegram_token_provider)

    @staticmethod
    async def on_shutdown(ctx: dict) -> None:
        """Cleanup worker resources."""


class SchedulerSettings:
    """ARQ scheduler with cron jobs for ETL and CRM batch processing.

    NOTE: arq's get_kwargs() uses __dict__ (not dir()), so inherited attributes
    are invisible. All settings must be defined directly on this class.
    """

    from luana_core_analytics_engine.workers.scheduler import run_tick_scheduler

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
        # PI-1 S2 PR-5 campaigns workers
        run_campaign_execution_task,
        run_campaign_scheduler_tick,
        run_segment_refresh_tick,
        purge_old_campaigns_audit,
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
        # PI-1 S2 PR-5 — campaign scheduler tick: promote scheduled campaigns
        # + claim pending tasks. Minute={5,15,25,35,45,55} (disjoint from
        # analytics run_tick_scheduler minute=range(60)).
        cron(
            run_campaign_scheduler_tick,
            minute={5, 15, 25, 35, 45, 55},
        ),
        # PI-1 S2 PR-5 — segment refresh tick: refresh stale STATIC segments
        # linked to RUNNING campaigns. Hourly at :20.
        cron(
            run_segment_refresh_tick,
            hour=set(range(24)),
            minute=20,
        ),
        # PI-1 S2 PR-5 — audit retention purge: hard-delete old campaign_audit
        # rows. 04:30 UTC (offset from copilot purge_expired_trace_rows 04:00).
        cron(
            purge_old_campaigns_audit,
            hour=4,
            minute=30,
        ),
    ]

    @staticmethod
    async def on_startup(ctx: dict) -> None:
        """Initialize DB session factory, Redis, and Sentry for scheduler."""
        from luana_core_copilot.application.extraction_card_flow import (
            register_extraction_event_handlers,
        )
        from luana_core_observability.recording.cost_recorder import (
            register_cost_recorder,
        )
        from luana_core_platform.application.brand_summary_event_handlers import (
            register_brand_summary_event_handlers,
        )
        from luana_core_platform.core.database import SessionLocal, redis_client
        from luana_core_platform.core.sentry import init_sentry

        init_sentry("scheduler")
        ctx["db_factory"] = SessionLocal
        ctx["redis_cache"] = redis_client
        register_extraction_event_handlers()
        register_brand_summary_event_handlers()

        # PI-12 S1 T-1 — process-wide LiteLLM CustomLogger for cost capture.
        # Scheduler triggers ARQ tasks that invoke LLMs; the recorder MUST
        # be registered here too (process-isolated from FastAPI + workers).
        register_cost_recorder()

        # S8 — bridge AppointmentEvent / BookingMissedEvent into
        # scheduled_meetings JSONB. Idempotent registration.
        from luana_core_sales_agent.application.scheduling_event_handlers import (
            register_scheduling_event_handlers,
        )

        register_scheduling_event_handlers()

        # PI-1 S2 PR-5 — campaigns channel registry bootstrap (mirror WorkerSettings).
        from luana_core_campaigns.infrastructure.channels.registry import (
            register_default_channels,
        )

        async def _env_telegram_token_provider(_tenant_id: object) -> str:
            import os

            return os.environ.get("TELEGRAM_BOT_TOKEN", "")

        register_default_channels(telegram_token_provider=_env_telegram_token_provider)

    @staticmethod
    async def on_shutdown(ctx: dict) -> None:
        """Cleanup scheduler resources."""
