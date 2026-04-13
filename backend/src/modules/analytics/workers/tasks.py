"""ARQ task functions for ETL extraction jobs and CRM batch processing.

All service imports are done lazily inside function bodies (late binding)
to avoid import-time issues when dependent modules haven't been executed yet.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

import sentry_sdk
import structlog
from arq import Retry
from sentry_sdk.crons import MonitorStatus, capture_checkin

from src.modules.analytics.application.config import CacheConfig

logger = structlog.get_logger(__name__)

# Fibonacci backoff intervals in minutes
FIBONACCI_BACKOFF = [1, 1, 2, 3, 5, 8, 13]


async def _maybe_enqueue_period_extraction(ctx: dict, db: Session, tenant_id: str) -> None:
    """Enqueue period extraction for current week+month if period_metrics is empty.

    Called after a successful daily ETL to bootstrap period data on first run.
    """
    from datetime import timedelta

    from sqlalchemy import func, select

    from src.shared.domain.datetime_utils import utc_today

    redis = ctx.get("redis")
    if not redis:
        return

    try:
        from src.modules.analytics.infrastructure.models.period_metrics_model import (
            PeriodMetricModel,
        )

        count = (
            db.execute(
                select(func.count()).where(PeriodMetricModel.tenant_id == tenant_id),
            ).scalar()
            or 0
        )

        if count > 0:
            return  # Already has period data

        today = utc_today()
        # Enqueue weekly: current week (Mon-Sun or custom)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        if week_end < today:
            await redis.enqueue_job(
                "run_period_extraction",
                tenant_id,
                "weekly",
                week_start.isoformat(),
                week_end.isoformat(),
            )

        # Enqueue monthly: previous month
        first_of_month = today.replace(day=1)
        last_month_end = first_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        await redis.enqueue_job(
            "run_period_extraction",
            tenant_id,
            "monthly",
            last_month_start.isoformat(),
            last_month_end.isoformat(),
        )

        logger.info(
            "Period extraction auto-triggered for tenant=%s (period_metrics was empty)",
            tenant_id,
        )
    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        logger.warning(
            "Failed to auto-trigger period extraction for tenant=%s: %s",
            tenant_id,
            str(exc),
        )


async def run_tenant_extraction(
    ctx: dict,
    tenant_id: str,
    provider: str,
) -> dict:
    """Execute ETL extraction for a single tenant and provider.

    On transient errors, retries with Fibonacci backoff.
    On ConnectionRevokedError, fails permanently (no retry).
    """
    from src.modules.analytics.domain.exceptions import ConnectionRevokedError

    db_factory = ctx["db_factory"]
    db = db_factory()

    check_in_id = capture_checkin(
        monitor_slug="etl-daily-extraction",
        status=MonitorStatus.IN_PROGRESS,
        monitor_config={
            "schedule": {"type": "interval", "value": 1, "unit": "hour"},
            "checkin_margin": 10,
            "max_runtime": 30,
        },
    )

    try:
        # Late imports to avoid circular/missing imports during development
        from src.modules.analytics.application.services.etl_service import ETLService
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        redis = ctx.get("redis_cache")
        cache = MetricsCache(redis)
        connection_port = ConnectionPortImpl(db)
        etl_service = ETLService(db=db, connection_port=connection_port, cache=cache)

        if provider == "all":
            await etl_service.run_all_providers(UUID(tenant_id))
        else:
            await etl_service.run_extraction(UUID(tenant_id), provider)

        logger.info(
            "Extraction completed for tenant=%s provider=%s",
            tenant_id,
            provider,
        )

        # Auto-trigger period extraction if period_metrics is empty
        await _maybe_enqueue_period_extraction(ctx, db, tenant_id)

        capture_checkin(
            monitor_slug="etl-daily-extraction",
            check_in_id=check_in_id,
            status=MonitorStatus.OK,
        )

    except ConnectionRevokedError as exc:
        # Permanent failure — do not retry revoked connections
        logger.exception(
            "Connection revoked for tenant=%s provider=%s",
            tenant_id,
            provider,
        )
        capture_checkin(
            monitor_slug="etl-daily-extraction",
            check_in_id=check_in_id,
            status=MonitorStatus.ERROR,
        )
        return {"status": "revoked", "tenant_id": tenant_id, "error": str(exc)}

    except Exception as exc:
        # Transient error — retry with Fibonacci backoff
        job_try = ctx.get("job_try", 1)
        fib_index = min(job_try - 1, len(FIBONACCI_BACKOFF) - 1)
        defer_seconds = FIBONACCI_BACKOFF[fib_index] * 60

        logger.warning(
            "Extraction failed for tenant=%s provider=%s (attempt %d), retrying in %d seconds: %s",
            tenant_id,
            provider,
            job_try,
            defer_seconds,
            str(exc),
        )
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("tenant_id", tenant_id)
            scope.set_tag("provider", provider)
            scope.set_tag("job_try", str(ctx.get("job_try", 1)))
            sentry_sdk.capture_exception(exc)
        capture_checkin(
            monitor_slug="etl-daily-extraction",
            check_in_id=check_in_id,
            status=MonitorStatus.ERROR,
        )
        raise Retry(defer=defer_seconds) from exc

    else:
        return {"status": "success", "tenant_id": tenant_id, "provider": provider}
    finally:
        db.close()


async def run_initial_load(
    ctx: dict,
    tenant_id: str,
    provider: str,
    initial_days: int = 7,
) -> dict:
    """Run initial extraction when a user connects a new provider.

    Extracts the last `initial_days` days of data immediately,
    without waiting for the next scheduled cron tick.
    """
    from src.modules.analytics.domain.exceptions import ConnectionRevokedError

    db_factory = ctx["db_factory"]
    db = db_factory()
    redis = ctx.get("redis_cache")
    progress_key = f"initial_load:{tenant_id}:{provider}"

    try:
        from src.modules.analytics.application.services.etl_service import ETLService
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        cache = MetricsCache(redis)
        connection_port = ConnectionPortImpl(db)
        etl_service = ETLService(db=db, connection_port=connection_port, cache=cache)

        def on_progress(loaded: int, total: int, status: str) -> None:
            if redis:
                redis.setex(
                    progress_key,
                    CacheConfig.CATALOG_TTL,
                    json.dumps(
                        {
                            "status": status,
                            "total_days": total,
                            "completed_days": loaded,
                        },
                    ),
                )

        on_progress(0, initial_days, "running")
        result = await etl_service.run_initial_load(
            UUID(tenant_id),
            provider,
            days=initial_days,
            progress_callback=on_progress,
        )
        on_progress(result["loaded"], result["total"], "completed")

        logger.info(
            "Initial load completed for tenant=%s provider=%s (last %d days)",
            tenant_id,
            provider,
            initial_days,
        )

    except ConnectionRevokedError as exc:
        logger.exception(
            "Connection revoked during initial load for tenant=%s provider=%s",
            tenant_id,
            provider,
        )
        if redis:
            redis.setex(
                progress_key,
                CacheConfig.CATALOG_TTL,
                json.dumps({"status": "failed", "error": str(exc)}),
            )
        return {"status": "revoked", "tenant_id": tenant_id, "error": str(exc)}

    except Exception as exc:
        job_try = ctx.get("job_try", 1)
        fib_index = min(job_try - 1, len(FIBONACCI_BACKOFF) - 1)
        defer_seconds = FIBONACCI_BACKOFF[fib_index] * 60

        logger.warning(
            "Initial load failed for tenant=%s provider=%s (attempt %d), retrying in %d seconds: %s",
            tenant_id,
            provider,
            job_try,
            defer_seconds,
            str(exc),
        )
        if redis:
            redis.setex(
                progress_key,
                CacheConfig.CATALOG_TTL,
                json.dumps({"status": "failed", "error": str(exc)}),
            )
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("tenant_id", tenant_id)
            scope.set_tag("provider", provider)
            scope.set_tag("job_try", str(ctx.get("job_try", 1)))
            sentry_sdk.capture_exception(exc)
        raise Retry(defer=defer_seconds) from exc

    else:
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "provider": provider,
            "initial_days": initial_days,
            **result,
        }
    finally:
        db.close()


async def run_period_extraction(
    ctx: dict,
    tenant_id: str,
    period_type: str,
    period_start: str,
    period_end: str,
) -> dict:
    """Extract NON_AGGREGABLE metrics for a complete period.

    Triggered by the scheduler when a period boundary is crossed,
    or manually via the API.
    """
    from datetime import date

    db_factory = ctx["db_factory"]
    db = db_factory()

    try:
        from src.modules.analytics.application.services.etl_service import ETLService
        from src.modules.analytics.infrastructure.cache.metrics_cache import (
            MetricsCache,
        )
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        redis = ctx.get("redis_cache")
        cache = MetricsCache(redis)
        connection_port = ConnectionPortImpl(db)
        etl_service = ETLService(db=db, connection_port=connection_port, cache=cache)

        results = await etl_service.run_period_extraction(
            tenant_id=UUID(tenant_id),
            period_type=period_type,
            period_start=date.fromisoformat(period_start),
            period_end=date.fromisoformat(period_end),
        )

        logger.info(
            "Period extraction completed for tenant=%s period=%s %s→%s results=%s",
            tenant_id,
            period_type,
            period_start,
            period_end,
            results,
        )

    except Exception as exc:
        job_try = ctx.get("job_try", 1)
        fib_index = min(job_try - 1, len(FIBONACCI_BACKOFF) - 1)
        defer_seconds = FIBONACCI_BACKOFF[fib_index] * 60

        logger.warning(
            "Period extraction failed for tenant=%s period=%s (attempt %d): %s",
            tenant_id,
            period_type,
            job_try,
            str(exc),
        )
        import sentry_sdk as _sentry

        with _sentry.push_scope() as scope:
            scope.set_tag("tenant_id", tenant_id)
            scope.set_tag("period_type", period_type)
            _sentry.capture_exception(exc)
        raise Retry(defer=defer_seconds) from exc

    else:
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "period_type": period_type,
            "results": results,
        }
    finally:
        db.close()


async def run_campaign_sync(
    ctx: dict,
    tenant_id: str,
    provider: str = "meta",
) -> dict:
    """Sync campaign hierarchy (campaigns, ad sets, ads, recommendations) from a provider.

    Separate from metrics ETL — this extracts campaign *structure*, not time-series data.
    On transient errors, retries with Fibonacci backoff.
    On ConnectionRevokedError, fails permanently (no retry).
    """
    from src.modules.analytics.domain.exceptions import ConnectionRevokedError

    db_factory = ctx["db_factory"]
    db = db_factory()

    try:
        from src.modules.analytics.infrastructure.providers.meta_campaign_provider import (
            MetaCampaignProvider,
        )
        from src.modules.analytics.infrastructure.repositories.campaign_repository import (
            CampaignRepository,
        )
        from src.modules.analytics.infrastructure.sync.campaign_sync_pipeline import (
            CampaignSyncPipeline,
        )
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        connection_port = ConnectionPortImpl(db)
        credentials = await connection_port.get_credentials(
            UUID(tenant_id),
            provider,
        )

        campaign_repo = CampaignRepository(db)
        campaign_provider = MetaCampaignProvider()
        pipeline = CampaignSyncPipeline(
            provider=campaign_provider,
            repository=campaign_repo,
        )

        result = await pipeline.run_sync(
            UUID(tenant_id),
            {**credentials.credentials, **credentials.config},
        )
        db.commit()

        sync_result = {
            "status": "success",
            "tenant_id": tenant_id,
            "provider": provider,
            **result,
        }

        # Store result in Redis for status polling
        redis_cache = ctx.get("redis_cache")
        if redis_cache:
            redis_cache.setex(
                f"campaign_sync:{tenant_id}:{provider}",
                3600,
                json.dumps(sync_result),
            )

        logger.info(
            "Campaign sync completed for tenant=%s provider=%s: %s",
            tenant_id,
            provider,
            result,
        )

    except ConnectionRevokedError as exc:
        logger.exception(
            "Connection revoked for campaign sync tenant=%s provider=%s",
            tenant_id,
            provider,
        )
        return {"status": "revoked", "tenant_id": tenant_id, "error": str(exc)}

    except Exception as exc:
        job_try = ctx.get("job_try", 1)
        fib_index = min(job_try - 1, len(FIBONACCI_BACKOFF) - 1)
        defer_seconds = FIBONACCI_BACKOFF[fib_index] * 60

        logger.warning(
            "Campaign sync failed for tenant=%s provider=%s (attempt %d), retrying in %d seconds: %s",
            tenant_id,
            provider,
            job_try,
            defer_seconds,
            str(exc),
        )
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("tenant_id", tenant_id)
            scope.set_tag("provider", provider)
            scope.set_tag("job_try", str(ctx.get("job_try", 1)))
            sentry_sdk.capture_exception(exc)
        raise Retry(defer=defer_seconds) from exc

    else:
        return sync_result
    finally:
        db.close()


async def run_mailerlite_etl_sync(ctx: dict) -> dict:
    """Backup ETL sync: fetch Mailerlite campaign stats every 6 hours.

    Retrieves recent campaign activity from Mailerlite API, finds events
    not yet recorded as journey_events (idempotent via campaign_id + subscriber_email
    deduplication), creates missing journey_events, and triggers score recalculation
    for affected profiles.

    This catches events missed by webhooks (webhook downtime, delivery failures).
    """
    logger.info("Starting Mailerlite ETL backup sync")
    db_factory = ctx.get("db_factory")
    if not db_factory:
        logger.error("No db_factory in context")
        return {"status": "error", "reason": "no_db_factory"}

    check_in_id = capture_checkin(
        monitor_slug="mailerlite-etl-sync",
        status=MonitorStatus.IN_PROGRESS,
        monitor_config={
            "schedule": {"type": "crontab", "value": "15 0,6,12,18 * * *"},
            "checkin_margin": 5,
            "max_runtime": 30,
        },
    )

    db = db_factory()
    try:
        connections = _get_active_mailerlite_connections(db)
        synced_count = await _sync_mailerlite_tenants(db, connections)

        logger.info(
            "Mailerlite ETL backup sync complete: %d events synced",
            synced_count,
        )
        capture_checkin(
            monitor_slug="mailerlite-etl-sync",
            check_in_id=check_in_id,
            status=MonitorStatus.OK,
        )

    except Exception as exc:
        logger.exception("Mailerlite ETL backup sync failed globally")
        sentry_sdk.capture_exception(exc)
        capture_checkin(
            monitor_slug="mailerlite-etl-sync",
            check_in_id=check_in_id,
            status=MonitorStatus.ERROR,
        )
        db.rollback()
        return {"status": "error", "reason": "global_failure"}

    else:
        return {"status": "ok", "synced": synced_count}
    finally:
        db.close()


def _get_active_mailerlite_connections(db: Session) -> list[ChannelConnectionModel]:
    """Fetch all active Mailerlite connections."""
    from sqlalchemy import and_, select

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    result = db.execute(
        select(ChannelConnectionModel).where(
            and_(
                ChannelConnectionModel.channel_type == "mailerlite",
                ChannelConnectionModel.is_active == True,
            ),
        ),
    )
    return result.scalars().all()


async def _sync_mailerlite_tenants(db: Session, connections: list[ChannelConnectionModel]) -> int:
    """Sync campaign activities for each tenant with a Mailerlite connection."""
    synced_count = 0
    for conn in connections:
        tenant_id = conn.tenant_id
        try:
            synced_count += await _sync_single_tenant(db, conn, tenant_id)
            db.commit()
        except Exception as e:
            logger.exception("Mailerlite ETL sync failed for tenant %s", tenant_id)
            sentry_sdk.capture_exception(e)
            db.rollback()
    return synced_count


async def _sync_single_tenant(db: Session, conn: ChannelConnectionModel, tenant_id: UUID) -> int:
    """Sync a single tenant's Mailerlite activities. Returns events synced."""
    from sqlalchemy import and_, select

    from src.modules.connections.infrastructure.marketing_connectors.mailerlite import (
        MailerLiteConnector,
    )

    api_key = conn.credentials.get("api_key") if conn.credentials else None
    if not api_key:
        logger.warning("No Mailerlite API key for tenant %s, skipping", tenant_id)
        return 0

    connector = MailerLiteConnector(api_key=api_key)

    if not hasattr(connector, "get_recent_campaign_activity"):
        logger.warning(
            "MailerLiteConnector.get_recent_campaign_activity() not implemented yet. "
            "Skipping tenant %s. Add method to connector when Mailerlite API "
            "integration is complete.",
            tenant_id,
        )
        return 0

    activities = await connector.get_recent_campaign_activity(hours=7)

    from src.modules.crm.application.services.lifecycle_service import (
        LifecycleService,
    )
    from src.modules.crm.infrastructure.models.customer_model import (
        CustomerProfileModel,
        JourneyEventModel,
    )

    lifecycle_svc = LifecycleService(db)
    synced = 0

    for activity in activities:
        email = activity.get("email")
        campaign_id = activity.get("campaign_id")
        event_type = activity.get("event_type")

        profile_result = db.execute(
            select(CustomerProfileModel).where(
                and_(
                    CustomerProfileModel.tenant_id == tenant_id,
                    CustomerProfileModel.primary_email == email,
                    CustomerProfileModel.is_inactive == False,
                ),
            ),
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            continue

        event_name = "email_opened" if event_type == "open" else "email_clicked"

        existing = db.execute(
            select(JourneyEventModel.id).where(
                and_(
                    JourneyEventModel.profile_id == profile.id,
                    JourneyEventModel.tenant_id == tenant_id,
                    JourneyEventModel.event_name == event_name,
                    JourneyEventModel.properties["campaign_id"].astext == str(campaign_id),
                ),
            ),
        )
        if existing.scalar_one_or_none():
            continue

        journey_event = JourneyEventModel(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name=event_name,
            event_type="track",
            properties={
                "campaign_id": str(campaign_id),
                "campaign_name": activity.get("campaign_name", ""),
                "source": "mailerlite_etl_sync",
            },
        )
        db.add(journey_event)
        lifecycle_svc.recalculate_score(profile.id, tenant_id)
        synced += 1

    return synced


async def run_manychat_subscriber_sync(
    ctx: dict,
    tenant_id: str,
) -> dict:
    """Sync ManyChat subscriber data into CRM profiles.

    Fetches subscriber details from ManyChat API and enriches
    CRM customer_profiles with tags, custom fields, and score data.
    """
    db_factory = ctx["db_factory"]
    db = db_factory()

    try:
        from src.modules.analytics.workers.manychat_sync import (
            sync_manychat_subscribers,
        )

        result = await sync_manychat_subscribers(UUID(tenant_id), db)

        logger.info(
            "ManyChat subscriber sync completed for tenant=%s: %s",
            tenant_id,
            result,
        )

    except Exception as exc:
        job_try = ctx.get("job_try", 1)
        if job_try < 3:
            logger.warning(
                "ManyChat sync failed for tenant=%s (attempt %d): %s",
                tenant_id,
                job_try,
                str(exc),
            )
            raise Retry(
                defer=CacheConfig.DETAIL_STAGE_TTL,
            ) from exc  # Retry in 5 minutes
        logger.exception(
            "ManyChat sync permanently failed for tenant=%s",
            tenant_id,
        )
        return {"status": "error", "error": str(exc)}

    else:
        return result
    finally:
        db.close()


async def run_inactivity_detection(ctx: dict) -> dict:
    """Batch job: flag inactive profiles and apply score decay.

    Runs daily via ARQ cron (4am UTC). Processes all tenants.
    Late-binding imports to avoid circular dependencies.
    """
    db_factory = ctx["db_factory"]
    db = db_factory()

    check_in_id = capture_checkin(
        monitor_slug="crm-inactivity-detection",
        status=MonitorStatus.IN_PROGRESS,
        monitor_config={
            "schedule": {"type": "crontab", "value": "0 4 * * *"},
            "checkin_margin": 5,
            "max_runtime": 15,
        },
    )

    try:
        from src.modules.crm.application.services.inactivity_service import (
            InactivityService,
        )

        service = InactivityService(db)
        result = service.run_batch()
        db.commit()

        logger.info(
            "Inactivity detection completed: %s",
            result,
        )
        capture_checkin(
            monitor_slug="crm-inactivity-detection",
            check_in_id=check_in_id,
            status=MonitorStatus.OK,
        )

    except Exception as exc:
        db.rollback()
        logger.exception("Inactivity detection batch job failed")
        sentry_sdk.capture_exception(exc)
        capture_checkin(
            monitor_slug="crm-inactivity-detection",
            check_in_id=check_in_id,
            status=MonitorStatus.ERROR,
        )
        raise

    else:
        return result
    finally:
        db.close()
