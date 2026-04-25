"""Backfill script — regenerate the brand-summary lighthouse for every tenant.

Run once after F3 ships to populate ``brand_summary`` from existing
``BrandSettings``. Idempotent: re-runs simply update the ``version``
counter on each row. Tenants whose brand is empty are skipped silently.

Usage::

    cd backend && .venv/bin/python scripts/backfill_brand_summaries.py
    cd backend && .venv/bin/python scripts/backfill_brand_summaries.py --tenant <UUID>

Reads tenants from the live DB so the script works in dev (Docker
compose) and prod via env-resolved ``DATABASE_URL``. Use the prod alias
only on a maintenance window — each call hits the LLM (FAST tier).
"""

from __future__ import annotations

import argparse
import logging
import sys
from uuid import UUID

from sqlalchemy import select

# Bootstrap mappers + import path early so this script works the same
# way as the worker.
import src.shared.infrastructure.model_registry  # noqa: F401
from src.core.database import SessionLocal
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.workers.brand_summary_regen import regen_brand_summary_sync

logger = logging.getLogger("backfill_brand_summaries")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _iter_tenants(db, only: UUID | None):
    if only is not None:
        return [db.execute(select(TenantModel).where(TenantModel.id == only)).scalar_one_or_none()]
    return list(db.execute(select(TenantModel).where(TenantModel.is_active.is_(True))).scalars().all())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tenant",
        help="UUID of a single tenant to backfill (default: all active).",
    )
    args = parser.parse_args()

    only = UUID(args.tenant) if args.tenant else None

    db = SessionLocal()
    try:
        tenants = _iter_tenants(db, only)
        if only is not None and (not tenants or tenants[0] is None):
            logger.error("Tenant %s not found", only)
            return 1

        ok = 0
        skipped = 0
        for tenant in tenants:
            if tenant is None:
                continue
            try:
                summary = regen_brand_summary_sync(
                    db=db,
                    tenant_id=tenant.id,
                    last_section_changed="backfill",
                )
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("backfill failed for tenant=%s", tenant.id)
                continue
            if summary is None:
                skipped += 1
                logger.info("skipped tenant=%s (empty brand)", tenant.id)
            else:
                ok += 1
                logger.info(
                    "persisted tenant=%s chars=%d",
                    tenant.id,
                    len(summary),
                )

        logger.info("backfill complete: ok=%d skipped=%d", ok, skipped)
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
