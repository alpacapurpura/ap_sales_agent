"""ARQ task functions for ETL extraction jobs.

All service imports are done lazily inside function bodies (late binding)
to avoid import-time issues when Plan 02's ETLService hasn't been executed yet.
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
