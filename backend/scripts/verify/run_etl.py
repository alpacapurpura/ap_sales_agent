"""Layer 0: Trigger ETL extraction for a provider and wait for completion.

Runs INSIDE the Docker container (visionarias_brain_dev) to have direct
access to the database and ETL service — no HTTP auth needed.

Usage (via Makefile — recommended):
    make verify-etl provider=meta days=7

Usage (direct — inside container):
    docker exec -t visionarias_brain_dev bash -c \
      "cd /app && python scripts/verify/run_etl.py --provider meta --days 7"

Usage (production — via SSH):
    ssh -p 22022 root@161.132.41.191 \
      'docker exec -t visionarias_brain_dev bash -c \
       "cd /app && python scripts/verify/run_etl.py --provider meta --days 7 --tenant-id UUID"'
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date, timedelta
from uuid import UUID

# Ensure src/ is importable when running as script inside container
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import redis_client
from src.modules.analytics.application.services.etl_service import (
    ETLService,
)
from src.modules.analytics.infrastructure.cache.metrics_cache import (
    MetricsCache,
)
from src.modules.connections.application.services.connection_port_impl import (
    ConnectionPortImpl,
)
from src.shared.infrastructure import model_registry  # noqa: F401


def _resolve_tenant_id(args_tid: str | None) -> str | None:
    return (
        args_tid
        or os.environ.get("VERIFY_TENANT_ID")
        or os.environ.get("E2E_TENANT_ID")
    )


async def run_extraction(tenant_id: str, provider_name: str, days: int) -> dict:
    """Run ETL extraction directly via ETLService."""
    engine = create_engine(str(settings.DATABASE_URL))
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    with Session(engine) as db:
        cache = MetricsCache(redis_client)
        connection_port = ConnectionPortImpl(db)
        etl = ETLService(db, connection_port=connection_port, cache=cache)

        try:
            run = await etl.run_extraction(
                tenant_id=UUID(tenant_id),
                provider_name=provider_name,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as exc:
            return {"status": "failed", "error": str(exc)}

        if run is None:
            return {"status": "failed", "error": "run_extraction returned None"}

        # Read attributes while session is still open
        return {
            "status": str(run.status) if hasattr(run, "status") else "unknown",
            "loaded": getattr(run, "metrics_loaded", 0),
            "skipped": getattr(run, "metrics_skipped", 0),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Layer 0: Trigger ETL extraction")
    parser.add_argument("--provider", required=True, help="Provider name (e.g. meta)")
    parser.add_argument(
        "--days", type=int, default=7, help="Days to extract (default 7)"
    )
    parser.add_argument(
        "--env",
        choices=["local", "prod"],
        default="local",
        help="Target environment (ignored — always runs against local DB)",
    )
    parser.add_argument("--tenant-id", default=None)
    args = parser.parse_args()

    tenant_id = _resolve_tenant_id(args.tenant_id)
    if not tenant_id:
        print(
            "ERROR: No tenant ID. Set VERIFY_TENANT_ID or E2E_TENANT_ID env var, "
            "or pass --tenant-id.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[Layer 0] Triggering ETL for provider={args.provider} "
        f"days={args.days} tenant={tenant_id}"
    )

    result = asyncio.run(run_extraction(tenant_id, args.provider, args.days))

    status = result.get("status", "unknown")
    loaded = result.get("loaded", 0)
    skipped = result.get("skipped", 0)

    if "fail" in status.lower():
        error = result.get("error", "unknown")
        print(f"[Layer 0] FAILED: {args.provider} — {error}", file=sys.stderr)
        return 1

    print(
        f"[Layer 0] SUCCESS: {args.provider} status={status} loaded={loaded} skipped={skipped}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
