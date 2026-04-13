"""ARQ task for polling domain verification status.

Finds domains in PENDING_VERIFICATION or VERIFYING state older than 5 minutes
and calls verify_domain() for each one to sync status from Cloudflare.
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import sentry_sdk
import structlog
from sentry_sdk.crons import MonitorStatus, capture_checkin

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

_PENDING_THRESHOLD_MINUTES = 5


async def poll_domain_verification(ctx: dict) -> dict:
    """Check Cloudflare status for all unresolved custom domains.

    Processes domains with status PENDING_VERIFICATION or VERIFYING that were
    created more than 5 minutes ago, to allow Cloudflare propagation time.
    """
    from sqlalchemy import select

    from src.modules.tenant_domains.application.domain_service import DomainService
    from src.modules.tenant_domains.domain.domain_entity import DomainStatus
    from src.modules.tenant_domains.infrastructure.models.tenant_domain_model import (
        TenantDomainModel,
    )

    db_factory = ctx.get("db_factory")
    if db_factory is None:
        logger.error("poll_domain_verification_no_db_factory")
        return {"processed": 0, "error": "no db_factory in context"}

    check_in_id = capture_checkin(
        monitor_slug="domain-verification-poll",
        status=MonitorStatus.IN_PROGRESS,
        monitor_config={
            "schedule": {"type": "crontab", "value": "*/5 * * * *"},
            "checkin_margin": 3,
            "max_runtime": 5,
        },
    )

    cutoff = datetime.now(UTC) - timedelta(minutes=_PENDING_THRESHOLD_MINUTES)
    pending_statuses = [DomainStatus.PENDING_VERIFICATION, DomainStatus.VERIFYING]

    db: Session = db_factory()
    try:
        stmt = select(TenantDomainModel).where(
            TenantDomainModel.status.in_(pending_statuses),
            TenantDomainModel.domain_type == "custom",
            TenantDomainModel.cloudflare_hostname_id.isnot(None),
            TenantDomainModel.created_at <= cutoff,
            TenantDomainModel.deleted_at.is_(None),
        )
        result = db.execute(stmt)
        candidates = result.scalars().all()

        processed = 0
        errors = 0
        service = DomainService(db)

        for record in candidates:
            try:
                service.verify_domain(
                    domain_id=record.id,
                    tenant_id=record.tenant_id,
                )
                processed += 1
                logger.info(
                    "domain_verification_polled",
                    domain_id=str(record.id),
                    tenant_id=str(record.tenant_id),
                    hostname=record.hostname,
                )
            except Exception as exc:  # noqa: BLE001 — worker task error boundary
                errors += 1
                sentry_sdk.capture_exception(exc)
                logger.warning(
                    "domain_verification_poll_failed",
                    domain_id=str(record.id),
                    hostname=record.hostname,
                    error=str(exc),
                )

        logger.info(
            "poll_domain_verification_complete",
            processed=processed,
            errors=errors,
            candidates=len(candidates),
        )
        capture_checkin(
            monitor_slug="domain-verification-poll",
            check_in_id=check_in_id,
            status=MonitorStatus.OK,
        )
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        capture_checkin(
            monitor_slug="domain-verification-poll",
            check_in_id=check_in_id,
            status=MonitorStatus.ERROR,
        )
        raise
    else:
        return {"processed": processed, "errors": errors}
    finally:
        db.close()
