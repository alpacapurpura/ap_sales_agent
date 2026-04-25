"""Brand summary provider — F3 lighthouse fetcher.

# [COPILOT-BRAND-SUMMARY-F3] -> docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md

Returns the persisted ``brand_summary.summary`` for the tenant, or
``None`` if no row exists yet (tenant freshly onboarded, regen never
ran). The system prompt builder treats ``None`` as "skip the
lighthouse" — there is no fallback to raw fields here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger(__name__)


class BrandSummaryProvider:
    """Returns a ≤800-char living brand summary."""

    async def summary(self, *, tenant_id: UUID) -> str | None:
        """Return the persisted brand summary for ``tenant_id`` or ``None``."""
        from src.core.database import SessionLocal
        from src.modules.brand.infrastructure.repositories.brand_summary_repository import (
            BrandSummaryRepository,
        )

        try:
            db = SessionLocal()
        except Exception:  # noqa: BLE001 — orchestrator resilience
            logger.warning("brand_summary_provider_db_unavailable", tenant_id=str(tenant_id))
            return None
        try:
            row = BrandSummaryRepository(db).get(tenant_id=tenant_id)
        except Exception:
            logger.exception("brand_summary_provider_fetch_failed", tenant_id=str(tenant_id))
            return None
        finally:
            db.close()

        if row is None:
            return None
        return row.summary
