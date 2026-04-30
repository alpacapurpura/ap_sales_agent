"""Refresh Meta Ads metrics for a tenant — wipe + re-extract + reconcile.

Recovers from contaminated official_metrics by:
1. Querying Meta Graph API directly to get the source-of-truth daily totals
2. Deleting all official_metrics rows for tenant + meta-ads + date range
3. Re-running the daily extraction pipeline (uses time_increment=1)
4. Comparing the post-load DB totals against Meta API totals
5. Reporting any discrepancies above a threshold

Idempotent: re-running on already-clean data is a no-op (DELETE matches 0 rows,
re-extraction upserts the same values).

Usage:
    docker exec -it visionarias_brain_dev bash -c \
      "cd /app && python scripts/refresh_meta_metrics_for_tenant.py \
       --tenant-id 6347e21e-8112-4aa1-80d3-6adaa73bf6f9 \
       --start 2026-03-12 --end 2026-04-09 [--dry-run]"

The script must run inside the backend container because it needs:
- DATABASE_URL pointing at the dev/prod Postgres
- ENCRYPTION_KEY env var to decrypt connection credentials
- All `src.modules.analytics.*` imports resolvable (PYTHONPATH setup)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import date
from uuid import UUID

import httpx
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import redis_client
from src.modules.analytics.application.services.etl_service import ETLService
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.providers.meta_provider import (
    GRAPH_API_BASE,
    _auth_headers,
)
from src.modules.connections.application.services.connection_port_impl import (
    ConnectionPortImpl,
)
from src.shared.infrastructure import (
    model_registry,  # noqa: F401  load all SQLAlchemy mappers
)

logger = structlog.get_logger(__name__)

# Discrepancies above this percentage trigger a warning in the report
RECONCILE_THRESHOLD_PCT = 1.0


@dataclass
class DailyTotals:
    """A single day's spend/impressions/clicks/reach across all granularities."""

    metric_date: date
    spend: float
    impressions: float
    clicks: float
    reach: float

    def diff_pct(self, other: DailyTotals, field: str) -> float:
        """Percentage difference for a field. Returns 0.0 if both are 0."""
        a = getattr(self, field)
        b = getattr(other, field)
        if a == 0 and b == 0:
            return 0.0
        if b == 0:
            return float("inf")
        return abs(a - b) / b * 100.0


# ---------------------------------------------------------------------------
# Meta API source of truth
# ---------------------------------------------------------------------------


async def fetch_meta_daily_totals(credentials: dict, start: date, end: date) -> dict[date, DailyTotals]:
    """Pull per-day account-level totals straight from Meta Insights API.

    Uses time_increment=1 → one row per day, indexed by date_start.
    Follows paging.next cursors so multi-month ranges are fetched in full.
    """
    access_token = credentials.get("access_token", "")
    ad_account_id = credentials.get("ad_account_id")
    if not ad_account_id or not access_token:
        raise RuntimeError("Missing ad_account_id or access_token in credentials")

    headers = _auth_headers(access_token)
    url: str | None = f"{GRAPH_API_BASE}/act_{ad_account_id}/insights"
    params: dict | None = {
        "fields": "spend,impressions,clicks,reach,date_start,date_stop",
        "time_range": json.dumps({"since": start.isoformat(), "until": end.isoformat()}),
        "time_increment": "1",
        "level": "account",
        "limit": "500",
    }

    rows: list[dict] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        page = 0
        while url is not None:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            payload = resp.json()
            rows.extend(payload.get("data", []))
            next_url = payload.get("paging", {}).get("next")
            url = next_url
            params = None  # next URL already includes the query string
            page += 1
            if page > 50:
                raise RuntimeError("Meta paging exceeded 50 pages, refusing to loop")

    totals: dict[date, DailyTotals] = {}
    for row in rows:
        ds = row.get("date_start")
        if not ds:
            continue
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            continue
        totals[d] = DailyTotals(
            metric_date=d,
            spend=float(row.get("spend", 0) or 0),
            impressions=float(row.get("impressions", 0) or 0),
            clicks=float(row.get("clicks", 0) or 0),
            reach=float(row.get("reach", 0) or 0),
        )
    return totals


# ---------------------------------------------------------------------------
# DB queries (reconciliation reads)
# ---------------------------------------------------------------------------


def fetch_db_daily_totals(db: Session, tenant_id: UUID, start: date, end: date) -> dict[date, DailyTotals]:
    """Read account-level rows (campaign_id IS NULL AND ad_id IS NULL AND ad_set_id IS NULL).

    Falls back to summing campaign-level rows when account-level is missing for a day.
    Mirrors the logic in get_channel_daily_metrics — must stay in sync with it.
    """
    METRICS = ("spend", "impressions", "clicks", "reach")

    sql = text(
        """
        SELECT metric_date, metric_name,
               SUM(value) FILTER (
                   WHERE campaign_id IS NULL AND ad_set_id IS NULL AND ad_id IS NULL
               ) AS account_only,
               SUM(value) FILTER (
                   WHERE campaign_id IS NOT NULL AND ad_set_id IS NULL AND ad_id IS NULL
               ) AS campaigns_sum
        FROM official_metrics
        WHERE tenant_id = :tid
          AND channel_slug = 'meta-ads'
          AND metric_name = ANY(:metrics)
          AND metric_date BETWEEN :start AND :end
        GROUP BY metric_date, metric_name
        ORDER BY metric_date
        """
    )
    rows = db.execute(
        sql,
        {"tid": str(tenant_id), "metrics": list(METRICS), "start": start, "end": end},
    ).all()

    by_day: dict[date, dict[str, float]] = {}
    for row in rows:
        d = row.metric_date
        name = row.metric_name
        # Prefer account-level, fallback to sum of campaigns
        value = row.account_only if row.account_only is not None else (row.campaigns_sum or 0)
        by_day.setdefault(d, {})[name] = float(value or 0)

    return {
        d: DailyTotals(
            metric_date=d,
            spend=metrics.get("spend", 0.0),
            impressions=metrics.get("impressions", 0.0),
            clicks=metrics.get("clicks", 0.0),
            reach=metrics.get("reach", 0.0),
        )
        for d, metrics in by_day.items()
    }


def count_meta_rows(db: Session, tenant_id: UUID, start: date, end: date) -> int:
    """Count all official_metrics rows for tenant+meta provider in range (any channel)."""
    return int(
        db.execute(
            text(
                "SELECT COUNT(*) FROM official_metrics "
                "WHERE tenant_id = :tid AND provider = 'meta' "
                "AND metric_date BETWEEN :start AND :end"
            ),
            {"tid": str(tenant_id), "start": start, "end": end},
        ).scalar()
        or 0
    )


def delete_meta_rows(db: Session, tenant_id: UUID, start: date, end: date) -> int:
    """Hard delete all meta-provider rows for the tenant in the date range.

    Wipes EVERY channel produced by the Meta provider (meta-ads, ig-organic,
    fb-organic, meta-retargeting). This is required because EtlService.run_initial_load
    detects gaps by tenant+provider — if any channel has rows for a day, ALL
    channels are skipped on re-extraction. Wiping the whole provider for the
    range guarantees a clean re-load.

    Recovery-only operation — bypasses soft delete because the rows are about
    to be overwritten with correct values from a fresh extraction.
    """
    result = db.execute(
        text(
            "DELETE FROM official_metrics "
            "WHERE tenant_id = :tid "
            "AND provider = 'meta' "
            "AND metric_date BETWEEN :start AND :end"
        ),
        {"tid": str(tenant_id), "start": start, "end": end},
    )
    return int(result.rowcount or 0)


# ---------------------------------------------------------------------------
# Reconciliation reporter
# ---------------------------------------------------------------------------


def print_reconciliation_table(meta: dict[date, DailyTotals], db: dict[date, DailyTotals]) -> int:
    """Print a side-by-side comparison. Returns the number of discrepancies."""
    all_dates = sorted(set(meta.keys()) | set(db.keys()))
    discrepancies = 0

    print()
    print("=" * 110)
    print(
        f"{'date':<12} | {'spend(meta)':>12} {'spend(db)':>12} {'Δ%':>8} | "
        f"{'impr(meta)':>10} {'impr(db)':>10} {'Δ%':>8}"
    )
    print("-" * 110)

    for d in all_dates:
        m = meta.get(d)
        b = db.get(d)
        if m and b:
            spend_diff = m.diff_pct(b, "spend")
            impr_diff = m.diff_pct(b, "impressions")
            ok = spend_diff <= RECONCILE_THRESHOLD_PCT and impr_diff <= RECONCILE_THRESHOLD_PCT
            marker = "✓" if ok else "⚠"
            print(
                f"{d.isoformat():<12} | "
                f"{m.spend:>12.2f} {b.spend:>12.2f} {spend_diff:>7.2f}% | "
                f"{m.impressions:>10.0f} {b.impressions:>10.0f} {impr_diff:>7.2f}% {marker}"
            )
            if not ok:
                discrepancies += 1
        elif m and not b:
            print(
                f"{d.isoformat():<12} | "
                f"{m.spend:>12.2f} {'MISSING':>12} ({'?':>7}) | "
                f"{m.impressions:>10.0f} {'MISSING':>10} ({'?':>7}) ⚠"
            )
            discrepancies += 1
        elif b and not m:
            print(
                f"{d.isoformat():<12} | "
                f"{'MISSING':>12} {b.spend:>12.2f} ({'?':>7}) | "
                f"{'MISSING':>10} {b.impressions:>10.0f} ({'?':>7}) ⚠"
            )
            discrepancies += 1
    print("-" * 110)

    meta_total_spend = sum(t.spend for t in meta.values())
    db_total_spend = sum(t.spend for t in db.values())
    print(f"{'TOTAL':<12} | {meta_total_spend:>12.2f} {db_total_spend:>12.2f}")
    print("=" * 110)
    print()

    return discrepancies


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True, type=UUID)
    parser.add_argument("--start", required=True, type=date.fromisoformat)
    parser.add_argument("--end", required=True, type=date.fromisoformat)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip DELETE + re-extraction. Only fetch Meta totals and DB totals, print diff.",
    )
    args = parser.parse_args()

    if args.start > args.end:
        print("ERROR: --start must be <= --end", file=sys.stderr)
        return 2

    # Build a sync engine for the cleanup queries (the script does not need async DB access).
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    print(f"Tenant: {args.tenant_id}")
    print(f"Range:  {args.start} → {args.end}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'EXECUTE'}")

    # 1. Load credentials via the same path the pipeline uses
    with Session(engine) as db:
        connection_port = ConnectionPortImpl(db)
        creds_obj = await connection_port.get_credentials(args.tenant_id, "meta")
        credentials = {**creds_obj.credentials, **creds_obj.config}

    # 2. Fetch Meta source-of-truth totals BEFORE touching the DB
    print("\n[1/5] Fetching source-of-truth daily totals from Meta API...")
    meta_totals = await fetch_meta_daily_totals(credentials, args.start, args.end)
    print(f"      Got {len(meta_totals)} days from Meta")

    # 3. Snapshot current DB state
    print("\n[2/5] Reading current DB state...")
    with Session(engine) as db:
        before_db_totals = fetch_db_daily_totals(db, args.tenant_id, args.start, args.end)
        before_row_count = count_meta_rows(db, args.tenant_id, args.start, args.end)
    print(f"      DB has {before_row_count} rows for tenant+meta-ads in range")

    print("\n[3/5] BEFORE state — Meta vs DB:")
    discrepancies_before = print_reconciliation_table(meta_totals, before_db_totals)
    print(f"Discrepancies BEFORE: {discrepancies_before}")

    if args.dry_run:
        print("\n--dry-run set; skipping DELETE + re-extraction.")
        return 0 if discrepancies_before == 0 else 1

    # 4. Wipe + re-extract
    print(f"\n[4/5] Deleting {before_row_count} rows and re-running daily extraction...")
    with Session(engine) as db:
        deleted = delete_meta_rows(db, args.tenant_id, args.start, args.end)
        db.commit()
        print(f"      Deleted {deleted} rows")

    # Use the production EtlService.run_initial_load — exactly the path that ETL uses for backfills.
    # The fix ensures it uses time_increment=1 throughout, so the new rows are correct.
    with Session(engine) as db:
        connection_port = ConnectionPortImpl(db)
        cache = MetricsCache(redis_client)
        service = ETLService(db=db, connection_port=connection_port, cache=cache)

        days = (args.end - args.start).days + 1
        result = await service.run_initial_load(
            tenant_id=args.tenant_id,
            provider_name="meta",
            days=days,
            stage="attraction",
        )
        print(f"      run_initial_load result: {result}")

    # 5. Verify post-load
    print("\n[5/5] Re-reading DB state and reconciling vs Meta...")
    with Session(engine) as db:
        after_db_totals = fetch_db_daily_totals(db, args.tenant_id, args.start, args.end)
        after_row_count = count_meta_rows(db, args.tenant_id, args.start, args.end)
    print(f"      DB has {after_row_count} rows after re-extraction")

    print("\nAFTER state — Meta vs DB:")
    discrepancies_after = print_reconciliation_table(meta_totals, after_db_totals)

    print(f"Discrepancies BEFORE: {discrepancies_before}")
    print(f"Discrepancies AFTER:  {discrepancies_after}")

    if discrepancies_after == 0:
        print("\n✓ Reconciliation clean. DB matches Meta API.")
        return 0
    print(
        f"\n⚠ {discrepancies_after} day(s) still diverge from Meta. "
        "Possible causes:\n"
        "  - Day not yet closed at Meta side (last day of range often shows as partial)\n"
        "  - Tracked metric set differs (we only verify spend/impressions)\n"
        "  - Currency conversion differences"
    )
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
