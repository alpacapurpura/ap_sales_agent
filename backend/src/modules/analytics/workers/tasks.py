"""ARQ task functions for ETL extraction jobs and CRM batch processing.

All service imports are done lazily inside function bodies (late binding)
to avoid import-time issues when dependent modules haven't been executed yet.
"""

import logging
from datetime import date, timedelta
from uuid import UUID

from arq import Retry

logger = logging.getLogger(__name__)

# Fibonacci backoff intervals in minutes
FIBONACCI_BACKOFF = [1, 1, 2, 3, 5, 8, 13]


async def run_tenant_extraction(
    ctx: dict,
    tenant_id: str,
    provider: str,
) -> dict:
    """Execute ETL extraction for a single tenant and provider.

    On transient errors, retries with Fibonacci backoff.
    On ConnectionRevokedException, fails permanently (no retry).
    """
    from src.modules.analytics.domain.exceptions import ConnectionRevokedException

    db_factory = ctx["db_factory"]
    db = db_factory()

    try:
        # Late imports to avoid circular/missing imports during development
        from src.modules.analytics.application.services.etl_service import ETLService

        etl_service = ETLService(db=db)
        result = await etl_service.run_extraction(UUID(tenant_id), provider)

        logger.info(
            "Extraction completed for tenant=%s provider=%s",
            tenant_id,
            provider,
        )
        return {"status": "success", "tenant_id": tenant_id, "provider": provider}

    except ConnectionRevokedException as exc:
        # Permanent failure — do not retry revoked connections
        logger.error(
            "Connection revoked for tenant=%s provider=%s: %s",
            tenant_id,
            provider,
            str(exc),
        )
        return {"status": "revoked", "tenant_id": tenant_id, "error": str(exc)}

    except Exception as exc:
        # Transient error — retry with Fibonacci backoff
        job_try = ctx.get("job_try", 1)
        fib_index = min(job_try - 1, len(FIBONACCI_BACKOFF) - 1)
        defer_seconds = FIBONACCI_BACKOFF[fib_index] * 60

        logger.warning(
            "Extraction failed for tenant=%s provider=%s (attempt %d), "
            "retrying in %d seconds: %s",
            tenant_id,
            provider,
            job_try,
            defer_seconds,
            str(exc),
        )
        raise Retry(defer=defer_seconds) from exc

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
    from src.modules.analytics.domain.exceptions import ConnectionRevokedException

    db_factory = ctx["db_factory"]
    db = db_factory()

    try:
        from src.modules.analytics.application.services.etl_service import ETLService

        etl_service = ETLService(db=db)
        start_date = date.today() - timedelta(days=initial_days)

        result = await etl_service.run_extraction(
            UUID(tenant_id), provider, start_date=start_date
        )

        logger.info(
            "Initial load completed for tenant=%s provider=%s (last %d days)",
            tenant_id,
            provider,
            initial_days,
        )
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "provider": provider,
            "initial_days": initial_days,
        }

    except ConnectionRevokedException as exc:
        logger.error(
            "Connection revoked during initial load for tenant=%s provider=%s: %s",
            tenant_id,
            provider,
            str(exc),
        )
        return {"status": "revoked", "tenant_id": tenant_id, "error": str(exc)}

    except Exception as exc:
        job_try = ctx.get("job_try", 1)
        fib_index = min(job_try - 1, len(FIBONACCI_BACKOFF) - 1)
        defer_seconds = FIBONACCI_BACKOFF[fib_index] * 60

        logger.warning(
            "Initial load failed for tenant=%s provider=%s (attempt %d), "
            "retrying in %d seconds: %s",
            tenant_id,
            provider,
            job_try,
            defer_seconds,
            str(exc),
        )
        raise Retry(defer=defer_seconds) from exc

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
    from sqlalchemy import select, and_

    logger.info("Starting Mailerlite ETL backup sync")
    db_factory = ctx.get("db_factory")
    if not db_factory:
        logger.error("No db_factory in context")
        return {"status": "error", "reason": "no_db_factory"}

    db = db_factory()
    try:
        # 1. Get all tenants with active Mailerlite connections
        from src.modules.connections.infrastructure.models.channel_connection_model import (
            ChannelConnectionModel,
        )

        result = db.execute(
            select(ChannelConnectionModel).where(
                and_(
                    ChannelConnectionModel.channel_type == "mailerlite",
                    ChannelConnectionModel.is_active == True,  # noqa: E712
                )
            )
        )
        connections = result.scalars().all()

        synced_count = 0
        for conn in connections:
            tenant_id = conn.tenant_id
            try:
                # 2. Initialize Mailerlite connector with tenant credentials
                from src.modules.connections.infrastructure.marketing_connectors.mailerlite import (
                    MailerLiteConnector,
                )

                api_key = conn.credentials.get("api_key") if conn.credentials else None
                if not api_key:
                    logger.warning(
                        "No Mailerlite API key for tenant %s, skipping",
                        tenant_id,
                    )
                    continue

                connector = MailerLiteConnector(api_key=api_key)

                # 3. Fetch recent campaign activity (last 7 hours to overlap with 6h interval)
                # NOTE: get_recent_campaign_activity() may not be implemented yet.
                if not hasattr(connector, "get_recent_campaign_activity"):
                    logger.warning(
                        "MailerLiteConnector.get_recent_campaign_activity() not implemented yet. "
                        "Skipping tenant %s. Add method to connector when Mailerlite API "
                        "integration is complete.",
                        tenant_id,
                    )
                    continue

                activities = await connector.get_recent_campaign_activity(hours=7)

                # 4. For each activity, check if journey_event already exists
                from src.modules.crm.infrastructure.models.customer_model import (
                    CustomerProfileModel,
                    JourneyEventModel,
                )
                from src.modules.crm.application.services.lifecycle_service import (
                    LifecycleService,
                )

                lifecycle_svc = LifecycleService(db)

                for activity in activities:
                    email = activity.get("email")
                    campaign_id = activity.get("campaign_id")
                    event_type = activity.get("event_type")  # "open" or "click"

                    # Look up profile by email
                    profile_result = db.execute(
                        select(CustomerProfileModel).where(
                            and_(
                                CustomerProfileModel.tenant_id == tenant_id,
                                CustomerProfileModel.primary_email == email,
                                CustomerProfileModel.is_inactive == False,  # noqa: E712
                            )
                        )
                    )
                    profile = profile_result.scalar_one_or_none()
                    if not profile:
                        continue

                    event_name = "email_opened" if event_type == "open" else "email_clicked"

                    # Dedup: check if this exact event already exists
                    from sqlalchemy.dialects.postgresql import JSONB

                    existing = db.execute(
                        select(JourneyEventModel.id).where(
                            and_(
                                JourneyEventModel.profile_id == profile.id,
                                JourneyEventModel.tenant_id == tenant_id,
                                JourneyEventModel.event_name == event_name,
                                JourneyEventModel.properties["campaign_id"].astext == str(campaign_id),
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue  # Already recorded

                    # 5. Create missing journey_event
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

                    # 6. Recalculate score for affected profile
                    lifecycle_svc.recalculate_score(profile.id, tenant_id)
                    synced_count += 1

                db.commit()
            except Exception as e:
                logger.error("Mailerlite ETL sync failed for tenant %s: %s", tenant_id, e)
                db.rollback()

        logger.info("Mailerlite ETL backup sync complete: %d events synced", synced_count)
        return {"status": "ok", "synced": synced_count}

    except Exception:
        logger.exception("Mailerlite ETL backup sync failed globally")
        db.rollback()
        return {"status": "error", "reason": "global_failure"}

    finally:
        db.close()


async def run_inactivity_detection(ctx: dict) -> dict:
    """Batch job: flag inactive profiles and apply score decay.

    Runs daily via ARQ cron (4am UTC). Processes all tenants.
    Late-binding imports to avoid circular dependencies.
    """
    db_factory = ctx["db_factory"]
    db = db_factory()

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
        return result

    except Exception:
        db.rollback()
        logger.exception("Inactivity detection batch job failed")
        raise

    finally:
        db.close()
