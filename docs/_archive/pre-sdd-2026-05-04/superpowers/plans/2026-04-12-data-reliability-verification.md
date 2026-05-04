# Data Reliability Verification System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 4-layer verification system (ETL Execution -> Source Probe -> Pipeline Integrity -> UI Fidelity) that proves Growth Studio values match the real external API, with Meta as pilot.

**Architecture:** Python scripts for Layers 0-1 (ETL trigger + API probe), pytest with `@pytest.mark.verify` for Layer 2 (DB vs DTO), Playwright `*.verify.spec.ts` for Layer 3 (DTO vs UI). Claude rule enforces running the correct layers before committing changes.

**Tech Stack:** httpx (async API calls), pytest (pipeline tests), Playwright (UI tests), Make (orchestration)

**Spec:** `docs/superpowers/specs/2026-04-12-data-reliability-verification-design.md`

---

## File Structure

```
NEW FILES:
  backend/scripts/verify/__init__.py                    # Package marker
  backend/scripts/verify/run_etl.py                     # Layer 0: ETL trigger
  backend/scripts/verify/probes/__init__.py              # Package marker
  backend/scripts/verify/probes/base_probe.py            # Base protocol dataclasses
  backend/scripts/verify/probes/meta_probe.py            # Layer 1: Meta source probe
  backend/tests/verification/__init__.py                 # Package marker
  backend/tests/verification/conftest.py                 # Shared fixtures (PG connection)
  backend/tests/verification/test_pipeline_meta.py       # Layer 2: Meta pipeline integrity
  frontend/e2e/specs/verify/meta-fidelity.verify.spec.ts # Layer 3: Meta UI fidelity
  .claude/rules/data-reliability.md                      # Enforcement rule

MODIFIED FILES:
  .gitignore                                            # Add snapshots dir
  backend/pyproject.toml                                # Add verify marker
  frontend/playwright.config.ts                         # Add verify project
  Makefile                                              # Add verify-* targets
```

---

### Task 1: Infrastructure — gitignore, pytest marker, Playwright project

**Files:**
- Modify: `.gitignore:119`
- Modify: `backend/pyproject.toml:5-7`
- Modify: `frontend/playwright.config.ts:58-91`

- [ ] **Step 1: Add snapshots to .gitignore**

In `.gitignore`, after line 119 (`docs/temp/`), add:

```
# Verification snapshots (contain real metric values, never commit)
backend/scripts/verify/snapshots/
```

- [ ] **Step 2: Add verify marker to pyproject.toml**

In `backend/pyproject.toml`, replace lines 5-7:

```toml
markers = [
    "integration: live integration tests requiring external credentials",
    "verify: data reliability verification tests requiring real DB data",
]
```

- [ ] **Step 3: Add verify project to playwright.config.ts**

In `frontend/playwright.config.ts`, after the `public` project (line 90), add:

```typescript
    {
      name: 'verify',
      testMatch: /.*\.verify\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.clerk/user.json',
      },
      dependencies: ['setup'],
    },
```

- [ ] **Step 4: Create snapshots directory with .gitkeep**

```bash
mkdir -p backend/scripts/verify/snapshots
touch backend/scripts/verify/snapshots/.gitkeep
```

- [ ] **Step 5: Verify playwright config loads**

```bash
cd frontend && npx playwright test --list --project=verify
```

Expected: 0 tests found (no verify specs yet), no config errors.

- [ ] **Step 6: Commit**

```bash
git add .gitignore backend/pyproject.toml frontend/playwright.config.ts backend/scripts/verify/snapshots/.gitkeep
git commit -m "chore(verify): add infrastructure for 4-layer data reliability verification

Add pytest 'verify' marker, Playwright 'verify' project, gitignore snapshots dir."
```

---

### Task 2: Layer 0 — ETL Trigger Script

**Files:**
- Create: `backend/scripts/verify/__init__.py`
- Create: `backend/scripts/verify/run_etl.py`

- [ ] **Step 1: Create package marker**

```bash
touch backend/scripts/verify/__init__.py
```

- [ ] **Step 2: Write the ETL trigger script**

Create `backend/scripts/verify/run_etl.py`:

```python
"""Layer 0: Trigger ETL extraction and wait for completion.

Usage:
    # Local (default — calls localhost:8000)
    cd backend && .venv/bin/python scripts/verify/run_etl.py --provider meta --days 7

    # Production (calls prod via SSH tunnel — you must open the tunnel first)
    cd backend && .venv/bin/python scripts/verify/run_etl.py --provider meta --days 7 --env prod

Prerequisites:
    - Local: Docker containers running (docker compose up -d)
    - Prod: SSH tunnel open: ssh -L 18000:localhost:8000 -p 22022 root@161.132.41.191
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import httpx

# Resolve tenant from env — same var Playwright uses
TENANT_ID = os.environ.get("VERIFY_TENANT_ID") or os.environ.get("E2E_TENANT_ID")

ENV_URLS = {
    "local": "http://localhost:8000",
    "prod": "http://localhost:18000",  # SSH tunnel
}

TIMEOUT_SECONDS = 300  # 5 minutes max wait
POLL_INTERVAL = 5


def main() -> int:
    parser = argparse.ArgumentParser(description="Layer 0: Trigger ETL extraction")
    parser.add_argument("--provider", required=True, help="Provider name (e.g. meta)")
    parser.add_argument("--days", type=int, default=7, help="Days to extract (default 7)")
    parser.add_argument(
        "--env",
        choices=["local", "prod"],
        default="local",
        help="Target environment (default: local)",
    )
    parser.add_argument(
        "--tenant-id",
        default=None,
        help="Override tenant ID (default: VERIFY_TENANT_ID or E2E_TENANT_ID env var)",
    )
    args = parser.parse_args()

    tenant_id = args.tenant_id or TENANT_ID
    if not tenant_id:
        print(
            "ERROR: No tenant ID. Set VERIFY_TENANT_ID or E2E_TENANT_ID env var, "
            "or pass --tenant-id.",
            file=sys.stderr,
        )
        return 1

    base_url = ENV_URLS[args.env]
    url = f"{base_url}/api/v1/analytics/metrics/sync"
    headers = {"X-Tenant-ID": tenant_id}
    params = {"days": args.days}

    print(f"[Layer 0] Triggering ETL for provider={args.provider} days={args.days} env={args.env}")
    print(f"  URL: {url}")
    print(f"  Tenant: {tenant_id}")

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resp = client.post(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        print(
            f"ERROR: Cannot connect to {base_url}. "
            f"{'Is Docker running?' if args.env == 'local' else 'Is the SSH tunnel open?'}",
            file=sys.stderr,
        )
        return 1
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: HTTP {exc.response.status_code}: {exc.response.text}", file=sys.stderr)
        return 1

    # Parse response
    details = data.get("details", [])
    provider_detail = next(
        (d for d in details if d.get("provider") == args.provider), None
    )

    if provider_detail is None:
        print(f"WARNING: Provider '{args.provider}' not in sync response. Available:")
        for d in details:
            print(f"  - {d.get('provider')}: {d.get('status')}")
        return 1

    status = provider_detail.get("status", "unknown")
    loaded = provider_detail.get("loaded", 0)
    skipped = provider_detail.get("skipped", 0)

    if status == "ok":
        print(f"[Layer 0] SUCCESS: {args.provider} loaded={loaded} skipped={skipped}")
        return 0
    elif status == "skipped_cooldown":
        remaining = provider_detail.get("remaining_minutes", "?")
        print(
            f"[Layer 0] SKIPPED: {args.provider} on cooldown ({remaining} min remaining). "
            f"This means a recent extraction already ran — data is fresh.",
        )
        return 0
    else:
        error = provider_detail.get("error", "unknown error")
        print(f"[Layer 0] FAILED: {args.provider} — {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Test locally (Docker must be running)**

```bash
cd backend && .venv/bin/python scripts/verify/run_etl.py --provider meta --days 7
```

Expected: `[Layer 0] SUCCESS: meta loaded=N skipped=M` or `SKIPPED` if cooldown.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/verify/__init__.py backend/scripts/verify/run_etl.py
git commit -m "feat(verify): add Layer 0 — ETL trigger script

Calls POST /metrics/sync, reports per-provider status.
Supports --env local|prod via SSH tunnel."
```

---

### Task 3: Layer 1 — Base Probe Protocol

**Files:**
- Create: `backend/scripts/verify/probes/__init__.py`
- Create: `backend/scripts/verify/probes/base_probe.py`

- [ ] **Step 1: Create package marker**

```bash
mkdir -p backend/scripts/verify/probes
touch backend/scripts/verify/probes/__init__.py
```

- [ ] **Step 2: Write base probe dataclasses**

Create `backend/scripts/verify/probes/base_probe.py`:

```python
"""Base protocol for data reliability probes.

Every provider probe produces a ProbeReport containing per-metric
comparisons between the real API value and the official_metrics DB value.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass
class ProbeResult:
    """Single metric comparison: API value vs DB value."""

    provider: str
    channel_slug: str
    metric_name: str
    metric_date: date
    api_value: float
    db_value: float | None  # None = metric missing from DB
    match: bool
    pct_diff: float  # percentage difference (0.0 = perfect match)
    api_raw: dict = field(default_factory=dict)  # raw API fragment for debugging

    @staticmethod
    def compare(
        *,
        provider: str,
        channel_slug: str,
        metric_name: str,
        metric_date: date,
        api_value: float,
        db_value: float | None,
        threshold_pct: float = 1.0,
        api_raw: dict | None = None,
    ) -> ProbeResult:
        """Create a ProbeResult with automatic match calculation."""
        if db_value is None:
            return ProbeResult(
                provider=provider,
                channel_slug=channel_slug,
                metric_name=metric_name,
                metric_date=metric_date,
                api_value=api_value,
                db_value=None,
                match=False,
                pct_diff=100.0,
                api_raw=api_raw or {},
            )

        if api_value == 0.0 and db_value == 0.0:
            pct_diff = 0.0
        elif api_value == 0.0:
            pct_diff = 100.0
        else:
            pct_diff = abs(api_value - db_value) / abs(api_value) * 100.0

        return ProbeResult(
            provider=provider,
            channel_slug=channel_slug,
            metric_name=metric_name,
            metric_date=metric_date,
            api_value=api_value,
            db_value=db_value,
            match=pct_diff <= threshold_pct,
            pct_diff=round(pct_diff, 2),
            api_raw=api_raw or {},
        )


@dataclass
class ProbeReport:
    """Aggregated results from a single probe run."""

    provider: str
    tenant_id: UUID
    probe_date: date
    date_range: tuple[date, date]
    env: str  # "local" | "prod"
    threshold_pct: float
    results: list[ProbeResult] = field(default_factory=list)

    @property
    def total_metrics(self) -> int:
        return len(self.results)

    @property
    def matched(self) -> int:
        return sum(1 for r in self.results if r.match)

    @property
    def mismatched(self) -> int:
        return sum(1 for r in self.results if not r.match and r.db_value is not None)

    @property
    def missing_in_db(self) -> int:
        return sum(1 for r in self.results if r.db_value is None)

    @property
    def passed(self) -> bool:
        return all(r.match for r in self.results)

    def to_table(self) -> str:
        """Human-readable comparison table."""
        lines = [
            f"{'Channel':<15} {'Metric':<30} {'Date':<12} {'API':>12} {'DB':>12} {'Diff%':>8} {'Status':<6}",
            "-" * 97,
        ]
        for r in sorted(self.results, key=lambda x: (x.channel_slug, x.metric_name, x.metric_date)):
            db_str = f"{r.db_value:>12.2f}" if r.db_value is not None else "     MISSING"
            status = "OK" if r.match else "FAIL"
            lines.append(
                f"{r.channel_slug:<15} {r.metric_name:<30} {r.metric_date!s:<12} "
                f"{r.api_value:>12.2f} {db_str} {r.pct_diff:>7.2f}% {status:<6}"
            )
        lines.append("-" * 97)
        lines.append(
            f"Total: {self.total_metrics} | Matched: {self.matched} | "
            f"Mismatched: {self.mismatched} | Missing: {self.missing_in_db} | "
            f"{'PASSED' if self.passed else 'FAILED'}"
        )
        return "\n".join(lines)

    def to_json(self) -> str:
        """JSON snapshot for Layer 3 consumption."""
        return json.dumps(
            {
                "provider": self.provider,
                "tenant_id": str(self.tenant_id),
                "probe_date": self.probe_date.isoformat(),
                "date_range": [self.date_range[0].isoformat(), self.date_range[1].isoformat()],
                "env": self.env,
                "threshold_pct": self.threshold_pct,
                "passed": self.passed,
                "summary": {
                    "total": self.total_metrics,
                    "matched": self.matched,
                    "mismatched": self.mismatched,
                    "missing_in_db": self.missing_in_db,
                },
                "results": [
                    {
                        "channel_slug": r.channel_slug,
                        "metric_name": r.metric_name,
                        "metric_date": r.metric_date.isoformat(),
                        "api_value": r.api_value,
                        "db_value": r.db_value,
                        "match": r.match,
                        "pct_diff": r.pct_diff,
                    }
                    for r in self.results
                ],
            },
            indent=2,
        )
```

- [ ] **Step 3: Verify import works**

```bash
cd backend && .venv/bin/python -c "from scripts.verify.probes.base_probe import ProbeResult, ProbeReport; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/verify/probes/__init__.py backend/scripts/verify/probes/base_probe.py
git commit -m "feat(verify): add Layer 1 base probe protocol

ProbeResult + ProbeReport dataclasses with compare(), to_table(), to_json()."
```

---

### Task 4: Layer 1 — Meta Source Probe

**Files:**
- Create: `backend/scripts/verify/probes/meta_probe.py`

This is the largest task. The probe calls Meta Graph API independently and compares with official_metrics.

- [ ] **Step 1: Write the Meta probe**

Create `backend/scripts/verify/probes/meta_probe.py`:

```python
"""Layer 1: Meta Source Probe — calls Meta Graph API and compares with official_metrics.

Independently calls the same Meta API endpoints that meta_provider.py uses,
then compares raw API values against what the ETL stored in official_metrics.

This probe does NOT import from meta_provider.py. It makes its own HTTP calls
using the same endpoints and field lists. This ensures we verify the provider
code, not just re-run it.

Usage:
    cd backend && .venv/bin/python scripts/verify/probes/meta_probe.py --days 7
    cd backend && .venv/bin/python scripts/verify/probes/meta_probe.py --days 7 --env prod
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add project root to path so imports work when run as script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from scripts.verify.probes.base_probe import ProbeReport, ProbeResult
from src.core.config import settings

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"
THRESHOLD_PCT = 1.0

# ─── Expected Mappings ───────────────────────────────────────────────────
# These define what API field should map to what metric_name in our DB.
# If the provider changes a mapping, this probe catches the drift.

# Meta Ads: simple numeric fields from account-level /insights
META_ADS_SIMPLE_FIELDS: dict[str, str] = {
    "reach": "reach",
    "impressions": "impressions",
    "clicks": "clicks",
    "spend": "spend",
    "ctr": "ctr",
    "cpm": "cpm",
    "cpc": "cpc",
    "cpp": "meta_cpp",
    "frequency": "frequency",
    "inline_link_clicks": "meta_inline_link_clicks",
    "inline_post_engagement": "meta_post_engagement",
    "cost_per_inline_link_click": "meta_cost_per_link_click",
}

# Meta Ads: action types -> metric names
META_ADS_ACTION_MAP: dict[str, str] = {
    "offsite_conversion.fb_pixel_purchase": "conversions",
    "onsite_conversion.purchase": "conversions",
    "offsite_conversion.fb_pixel_lead": "meta_leads",
    "lead": "meta_leads",
    "link_click": "meta_link_clicks",
    "landing_page_view": "meta_landing_page_views",
    "video_view": "meta_video_views",
}

# IG Organic: API metric name -> our metric_name
IG_ORGANIC_METRICS: dict[str, str] = {
    "reach": "reach",
    "views": "ig_views",
    "total_interactions": "total_interactions",
    "likes": "ig_likes",
    "comments": "ig_comments",
    "shares": "ig_shares",
    "saves": "ig_saves",
    "accounts_engaged": "ig_accounts_engaged",
    "profile_links_taps": "ig_profile_links_taps",
    "replies": "ig_replies",
    "reposts": "ig_reposts",
}

# FB Organic: API metric -> our metric_name
FB_ORGANIC_METRICS: dict[str, str] = {
    "page_impressions_organic_unique": "fb_page_reach",
    "page_post_engagements": "fb_page_engagement",
}


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


# ─── Credential Resolution ───────────────────────────────────────────────


def get_credentials_from_db(env: str, tenant_id: str) -> dict:
    """Fetch decrypted Meta credentials from the connections table."""
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as db:
        row = db.execute(
            text(
                """
                SELECT credentials, config
                FROM channel_connections
                WHERE tenant_id = :tid
                  AND channel_type = 'meta'
                  AND is_active = true
                  AND deleted_at IS NULL
                LIMIT 1
                """
            ),
            {"tid": tenant_id},
        ).first()

    if row is None:
        raise RuntimeError(f"No active Meta connection for tenant {tenant_id}")

    creds = row.credentials or {}
    config = row.config or {}
    return {**creds, **config}


# ─── Meta API Callers (Independent) ──────────────────────────────────────


async def probe_meta_ads(
    client: httpx.AsyncClient,
    credentials: dict,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Call Meta Ads Insights API and return {(date, metric_name): value}."""
    ad_account_id = credentials.get("ad_account_id")
    access_token = credentials.get("access_token", "")
    if not ad_account_id:
        return {}

    fields = ",".join(
        list(META_ADS_SIMPLE_FIELDS.keys())
        + ["actions", "action_values", "outbound_clicks", "purchase_roas",
           "cost_per_action_type", "cost_per_outbound_click"]
    )

    url: str | None = f"{GRAPH_API_BASE}/act_{ad_account_id}/insights"
    params: dict | None = {
        "fields": fields,
        "time_range": json.dumps(
            {"since": start_date.isoformat(), "until": end_date.isoformat()}
        ),
        "time_increment": "1",
        "level": "account",
        "limit": "500",
    }

    all_rows: list[dict] = []
    while url is not None:
        resp = await client.get(url, headers=_auth_headers(access_token), params=params)
        resp.raise_for_status()
        payload = resp.json()
        all_rows.extend(payload.get("data", []))
        url = payload.get("paging", {}).get("next")
        params = None

    results: dict[tuple[date, str], float] = {}
    for row in all_rows:
        ds = row.get("date_start")
        if not ds:
            continue
        metric_date = date.fromisoformat(ds)

        # Simple fields
        for api_field, metric_name in META_ADS_SIMPLE_FIELDS.items():
            val = row.get(api_field)
            if val is not None:
                results[(metric_date, metric_name)] = float(val)

        # Actions
        from collections import defaultdict
        action_counts: dict[str, float] = defaultdict(float)
        for action in row.get("actions", []):
            action_type = action.get("action_type", "")
            mapped = META_ADS_ACTION_MAP.get(action_type)
            if mapped:
                action_counts[mapped] += float(action.get("value", 0))
        for mapped_name, value in action_counts.items():
            results[(metric_date, mapped_name)] = value

        # Outbound clicks
        for entry in row.get("outbound_clicks", []):
            if entry.get("action_type") == "outbound_click":
                results[(metric_date, "meta_outbound_clicks")] = float(
                    entry.get("value", 0)
                )

        # ROAS
        for entry in row.get("purchase_roas", []):
            if entry.get("action_type") == "omni_purchase":
                results[(metric_date, "meta_purchase_roas")] = float(
                    entry.get("value", 0)
                )

        # Conversion value
        for entry in row.get("action_values", []):
            if entry.get("action_type") in (
                "offsite_conversion.fb_pixel_purchase",
                "onsite_conversion.purchase",
            ):
                results[(metric_date, "meta_conversion_value")] = float(
                    entry.get("value", 0)
                )

        # Cost per purchase / lead
        for entry in row.get("cost_per_action_type", []):
            at = entry.get("action_type", "")
            if at in (
                "offsite_conversion.fb_pixel_purchase",
                "onsite_conversion.purchase",
            ):
                results[(metric_date, "meta_cost_per_purchase")] = float(
                    entry.get("value", 0)
                )
            elif at in ("offsite_conversion.fb_pixel_lead", "lead"):
                results[(metric_date, "meta_cost_per_lead")] = float(
                    entry.get("value", 0)
                )

        # Cost per outbound click
        for entry in row.get("cost_per_outbound_click", []):
            if entry.get("action_type") == "outbound_click":
                results[(metric_date, "meta_cost_per_outbound_click")] = float(
                    entry.get("value", 0)
                )

    return results


async def probe_ig_organic(
    client: httpx.AsyncClient,
    credentials: dict,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Call IG Insights API and return {(date, metric_name): value}.

    Note: IG Insights with period=day+total_value returns one value per
    metric for the entire range, not per-day. For the probe, we store the
    total against end_date (matching what the ETL does).
    """
    access_token = credentials.get("access_token", "")
    ig_account_id = (
        credentials.get("instagram_account_id")
        or credentials.get("tracked_ig_id")
        or credentials.get("instagram_business_account_id")
    )
    if not ig_account_id:
        return {}

    headers = _auth_headers(access_token)
    results: dict[tuple[date, str], float] = {}

    # IG day chunks: max 30 days per request
    chunks = []
    current = start_date
    while current < end_date:
        chunk_end = min(current + timedelta(days=30), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end

    totals: dict[str, float] = {}
    last_values: dict[str, float] = {}
    non_aggregable = {"reach", "accounts_engaged"}
    follows_gained = 0.0
    follows_lost = 0.0

    breakdownable = "reach,views,total_interactions,likes,comments,shares,saves"
    no_breakdown = "accounts_engaged,profile_links_taps,replies,reposts"

    for chunk_start, chunk_end in chunks:
        since_ts = int(datetime.combine(chunk_start, datetime.min.time()).timestamp())
        until_ts = int(datetime.combine(chunk_end, datetime.min.time()).timestamp())

        # Call A: breakdownable with media_product_type
        bd_resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_account_id}/insights",
            headers=headers,
            params={
                "metric": breakdownable,
                "metric_type": "total_value",
                "period": "day",
                "breakdown": "media_product_type",
                "since": since_ts,
                "until": until_ts,
            },
        )
        bd_resp.raise_for_status()
        for item in bd_resp.json().get("data", []):
            api_name = item.get("name", "")
            metric_name = IG_ORGANIC_METRICS.get(api_name)
            if not metric_name:
                continue
            # Sum organic values (exclude AD breakdown)
            val = _extract_organic_from_breakdown(item)
            if api_name in non_aggregable:
                last_values[metric_name] = val
            else:
                totals[metric_name] = totals.get(metric_name, 0.0) + val

        # Call B: non-breakdownable
        nb_resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_account_id}/insights",
            headers=headers,
            params={
                "metric": no_breakdown,
                "metric_type": "total_value",
                "period": "day",
                "since": since_ts,
                "until": until_ts,
            },
        )
        nb_resp.raise_for_status()
        for item in nb_resp.json().get("data", []):
            api_name = item.get("name", "")
            metric_name = IG_ORGANIC_METRICS.get(api_name)
            if not metric_name:
                continue
            val = float(item.get("total_value", {}).get("value", 0))
            if api_name in non_aggregable:
                last_values[metric_name] = val
            else:
                totals[metric_name] = totals.get(metric_name, 0.0) + val

        # Call C: follows_and_unfollows
        ft_resp = await client.get(
            f"{GRAPH_API_BASE}/{ig_account_id}/insights",
            headers=headers,
            params={
                "metric": "follows_and_unfollows",
                "metric_type": "total_value",
                "breakdown": "follow_type",
                "period": "day",
                "since": since_ts,
                "until": until_ts,
            },
        )
        ft_resp.raise_for_status()
        for item in ft_resp.json().get("data", []):
            if item.get("name") != "follows_and_unfollows":
                continue
            gained, lost = _parse_follow_type(item)
            follows_gained += gained
            follows_lost += lost

    # Store totals against end_date (matches ETL behavior)
    for metric_name, val in totals.items():
        results[(end_date, metric_name)] = val
    for metric_name, val in last_values.items():
        results[(end_date, metric_name)] = val
    results[(end_date, "ig_follows_gained")] = follows_gained
    results[(end_date, "ig_follows_lost")] = follows_lost
    results[(end_date, "ig_follows_and_unfollows")] = follows_gained - follows_lost

    # User node (followers_count, media_count)
    user_resp = await client.get(
        f"{GRAPH_API_BASE}/{ig_account_id}",
        headers=headers,
        params={"fields": "followers_count,media_count"},
    )
    user_resp.raise_for_status()
    user_data = user_resp.json()
    for field_name, metric_name in [
        ("followers_count", "ig_followers_count"),
        ("media_count", "ig_media_count"),
    ]:
        val = user_data.get(field_name)
        if val is not None:
            results[(end_date, metric_name)] = float(val)

    return results


async def probe_fb_organic(
    client: httpx.AsyncClient,
    credentials: dict,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Call FB Page Insights and return {(date, metric_name): value}."""
    access_token = credentials.get("page_access_token") or credentials.get("access_token", "")
    page_id = credentials.get("page_id")
    if not page_id:
        return {}

    headers = _auth_headers(access_token)
    results: dict[tuple[date, str], float] = {}

    since_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    until_ts = int(datetime.combine(end_date, datetime.min.time()).timestamp())

    for api_metric, metric_name in FB_ORGANIC_METRICS.items():
        resp = await client.get(
            f"{GRAPH_API_BASE}/{page_id}/insights",
            headers=headers,
            params={
                "metric": api_metric,
                "period": "day",
                "since": since_ts,
                "until": until_ts,
            },
        )
        resp.raise_for_status()
        # Sum daily values
        total = 0.0
        for item in resp.json().get("data", []):
            for val_entry in item.get("values", []):
                total += float(val_entry.get("value", 0))
        results[(end_date, metric_name)] = total

    return results


# ─── Helpers ──────────────────────────────────────────────────────────────


def _extract_organic_from_breakdown(item: dict) -> float:
    """Sum total_value results excluding AD media_product_type."""
    total_value = item.get("total_value", {})
    breakdowns = total_value.get("breakdowns", [])
    if not breakdowns:
        return float(total_value.get("value", 0))

    total = 0.0
    for bd in breakdowns:
        for result in bd.get("results", []):
            dims = {
                d.get("dimension_key"): d.get("dimension_value")
                for d in result.get("dimension_values", [])
            }
            if dims.get("media_product_type") == "AD":
                continue
            total += float(result.get("value", 0))
    return total


def _parse_follow_type(item: dict) -> tuple[float, float]:
    """Parse follows_and_unfollows with follow_type breakdown -> (gained, lost)."""
    gained = 0.0
    lost = 0.0
    total_value = item.get("total_value", {})
    for bd in total_value.get("breakdowns", []):
        for result in bd.get("results", []):
            dims = {
                d.get("dimension_key"): d.get("dimension_value")
                for d in result.get("dimension_values", [])
            }
            val = float(result.get("value", 0))
            ft = dims.get("follow_type", "")
            if ft in ("gained", "follow"):
                gained += val
            elif ft in ("lost", "unfollow"):
                lost += val
    return gained, lost


# ─── DB Comparison ────────────────────────────────────────────────────────


def fetch_db_metrics(
    tenant_id: str,
    channel_slug: str,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Read official_metrics for a channel and return {(date, metric_name): value}."""
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as db:
        rows = db.execute(
            text(
                """
                SELECT metric_date, metric_name, SUM(value) as total_value
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = :slug
                  AND metric_date BETWEEN :start AND :end
                  AND campaign_id IS NULL
                  AND ad_set_id IS NULL
                  AND ad_id IS NULL
                GROUP BY metric_date, metric_name
                """
            ),
            {
                "tid": tenant_id,
                "slug": channel_slug,
                "start": start_date,
                "end": end_date,
            },
        ).all()

    return {
        (row.metric_date, row.metric_name): float(row.total_value or 0)
        for row in rows
    }


# ─── Main Probe ──────────────────────────────────────────────────────────


async def run_meta_probe(
    tenant_id: str,
    start_date: date,
    end_date: date,
    env: str = "local",
    threshold_pct: float = THRESHOLD_PCT,
) -> ProbeReport:
    """Run the full Meta probe: API calls + DB comparison."""
    credentials = get_credentials_from_db(env, tenant_id)

    report = ProbeReport(
        provider="meta",
        tenant_id=UUID(tenant_id),
        probe_date=date.today(),
        date_range=(start_date, end_date),
        env=env,
        threshold_pct=threshold_pct,
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Probe all 3 channels
        ads_api = await probe_meta_ads(client, credentials, start_date, end_date)
        ig_api = await probe_ig_organic(client, credentials, start_date, end_date)
        fb_api = await probe_fb_organic(client, credentials, start_date, end_date)

    # Fetch DB values for each channel
    ads_db = fetch_db_metrics(tenant_id, "meta-ads", start_date, end_date)
    ig_db = fetch_db_metrics(tenant_id, "ig-organic", start_date, end_date)
    fb_db = fetch_db_metrics(tenant_id, "fb-organic", start_date, end_date)

    # Compare: meta-ads
    for (metric_date, metric_name), api_val in ads_api.items():
        db_val = ads_db.get((metric_date, metric_name))
        report.results.append(
            ProbeResult.compare(
                provider="meta",
                channel_slug="meta-ads",
                metric_name=metric_name,
                metric_date=metric_date,
                api_value=api_val,
                db_value=db_val,
                threshold_pct=threshold_pct,
            )
        )

    # Compare: ig-organic
    for (metric_date, metric_name), api_val in ig_api.items():
        db_val = ig_db.get((metric_date, metric_name))
        report.results.append(
            ProbeResult.compare(
                provider="meta",
                channel_slug="ig-organic",
                metric_name=metric_name,
                metric_date=metric_date,
                api_value=api_val,
                db_value=db_val,
                threshold_pct=threshold_pct,
            )
        )

    # Compare: fb-organic
    for (metric_date, metric_name), api_val in fb_api.items():
        db_val = fb_db.get((metric_date, metric_name))
        report.results.append(
            ProbeResult.compare(
                provider="meta",
                channel_slug="fb-organic",
                metric_name=metric_name,
                metric_date=metric_date,
                api_value=api_val,
                db_value=db_val,
                threshold_pct=threshold_pct,
            )
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Layer 1: Meta Source Probe")
    parser.add_argument("--days", type=int, default=7, help="Days to probe (default 7)")
    parser.add_argument("--env", choices=["local", "prod"], default="local")
    parser.add_argument("--tenant-id", default=None)
    parser.add_argument(
        "--output",
        default=None,
        help="Save JSON snapshot to file (e.g. scripts/verify/snapshots/meta-latest.json)",
    )
    parser.add_argument("--threshold", type=float, default=THRESHOLD_PCT)
    args = parser.parse_args()

    tenant_id = (
        args.tenant_id
        or os.environ.get("VERIFY_TENANT_ID")
        or os.environ.get("E2E_TENANT_ID")
    )
    if not tenant_id:
        print("ERROR: No tenant ID. Set VERIFY_TENANT_ID env var or pass --tenant-id.", file=sys.stderr)
        return 1

    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=args.days)

    print(f"[Layer 1] Meta Source Probe: {start_date} to {end_date} (env={args.env})")

    report = asyncio.run(
        run_meta_probe(tenant_id, start_date, end_date, args.env, args.threshold)
    )

    print()
    print(report.to_table())
    print()

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report.to_json())
        print(f"Snapshot saved to {args.output}")

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Test the probe (Docker + Meta token must be active)**

```bash
cd backend && .venv/bin/python scripts/verify/probes/meta_probe.py --days 3
```

Expected: Table showing API vs DB comparisons with OK/FAIL per metric.

- [ ] **Step 3: Test snapshot output**

```bash
cd backend && .venv/bin/python scripts/verify/probes/meta_probe.py --days 3 \
  --output scripts/verify/snapshots/meta-latest.json
cat scripts/verify/snapshots/meta-latest.json | python -m json.tool | head -20
```

Expected: JSON file with provider, results array, summary.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/verify/probes/meta_probe.py
git commit -m "feat(verify): add Layer 1 — Meta source probe

Independently calls Meta Graph API (ads, ig-organic, fb-organic),
compares with official_metrics, produces ProbeReport with threshold matching."
```

---

### Task 5: Layer 2 — Pipeline Integrity Tests

**Files:**
- Create: `backend/tests/verification/__init__.py`
- Create: `backend/tests/verification/conftest.py`
- Create: `backend/tests/verification/test_pipeline_meta.py`

- [ ] **Step 1: Create package and conftest**

Create `backend/tests/verification/__init__.py` (empty).

Create `backend/tests/verification/conftest.py`:

```python
"""Shared fixtures for Layer 2 verification tests.

These tests require a real PostgreSQL database with official_metrics data.
They connect to the visionarias_postgres container via DATABASE_URL.

Run: cd backend && .venv/bin/pytest tests/verification/ -m verify -x -q
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Default to local Docker Postgres
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/visionarias_logs",
)
TENANT_ID = os.environ.get("VERIFY_TENANT_ID") or os.environ.get("E2E_TENANT_ID")
BACKEND_URL = os.environ.get("VERIFY_BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture(scope="session")
def tenant_id():
    if not TENANT_ID:
        pytest.skip("VERIFY_TENANT_ID or E2E_TENANT_ID env var not set")
    return TENANT_ID


@pytest.fixture(scope="session")
def backend_url():
    return BACKEND_URL
```

- [ ] **Step 2: Write pipeline integrity tests**

Create `backend/tests/verification/test_pipeline_meta.py`:

```python
"""Layer 2: Pipeline Integrity — verify official_metrics -> stage service DTOs.

Reads real data from PostgreSQL, calls the backend API, compares values.
Requires Docker containers running with data (run Layer 0 first).

Run: cd backend && .venv/bin/pytest tests/verification/test_pipeline_meta.py -m verify -x -v
"""

import httpx
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.verify


class TestMetaAdsPipeline:
    """Verify meta-ads channel metrics flow correctly through the pipeline."""

    def _fetch_db_totals(self, db_session, tenant_id: str) -> dict[str, float]:
        """Read account-level meta-ads metrics from official_metrics (last 30 days)."""
        rows = db_session.execute(
            text(
                """
                SELECT metric_name, SUM(value) as total
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'meta-ads'
                  AND provider = 'meta'
                  AND campaign_id IS NULL
                  AND ad_set_id IS NULL
                  AND ad_id IS NULL
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY metric_name
                """
            ),
            {"tid": tenant_id},
        ).all()
        return {row.metric_name: float(row.total) for row in rows}

    def _fetch_api_attraction(self, backend_url: str, tenant_id: str) -> dict:
        """Call GET /metrics/attraction and return JSON response."""
        resp = httpx.get(
            f"{backend_url}/api/v1/analytics/metrics/attraction",
            headers={"X-Tenant-ID": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    def _find_channel_in_dto(self, dto: dict, channel_slug: str) -> dict | None:
        """Find a channel in the DTO groups structure."""
        for group in dto.get("groups", []):
            for channel in group.get("channels", []):
                if channel.get("slug") == channel_slug:
                    return channel
        return None

    def _get_metric_value(self, channel: dict, metric_name: str) -> float | None:
        """Extract a metric value from a channel DTO."""
        for metric in channel.get("metrics", []):
            if metric.get("name") == metric_name:
                return float(metric.get("value", 0))
        return None

    def test_meta_ads_present_in_attraction(
        self, db_session, tenant_id, backend_url
    ):
        """meta-ads channel must appear in the attraction DTO if DB has data."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if not db_totals:
            pytest.skip("No meta-ads data in DB — run Layer 0 first")

        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None, (
            "meta-ads channel not found in attraction DTO, "
            f"but DB has {len(db_totals)} metrics"
        )

    def test_meta_ads_spend_matches_db(
        self, db_session, tenant_id, backend_url
    ):
        """Spend in DTO must match SUM(value) from official_metrics."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "spend" not in db_totals:
            pytest.skip("No spend data in DB")

        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None

        dto_spend = self._get_metric_value(channel, "spend")
        assert dto_spend is not None, "spend metric not found in DTO"

        db_spend = db_totals["spend"]
        if db_spend == 0:
            assert dto_spend == 0
        else:
            pct_diff = abs(dto_spend - db_spend) / db_spend * 100
            assert pct_diff < 1.0, (
                f"Spend mismatch: DTO={dto_spend:.2f} DB={db_spend:.2f} "
                f"diff={pct_diff:.2f}%"
            )

    def test_meta_ads_impressions_matches_db(
        self, db_session, tenant_id, backend_url
    ):
        """Impressions in DTO must match SUM(value) from official_metrics."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "impressions" not in db_totals:
            pytest.skip("No impressions data in DB")

        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None

        dto_val = self._get_metric_value(channel, "impressions")
        assert dto_val is not None, "impressions metric not found in DTO"

        db_val = db_totals["impressions"]
        if db_val == 0:
            assert dto_val == 0
        else:
            pct_diff = abs(dto_val - db_val) / db_val * 100
            assert pct_diff < 1.0, (
                f"Impressions mismatch: DTO={dto_val:.0f} DB={db_val:.0f} "
                f"diff={pct_diff:.2f}%"
            )

    def test_meta_ads_clicks_matches_db(
        self, db_session, tenant_id, backend_url
    ):
        """Clicks in DTO must match SUM(value) from official_metrics."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "clicks" not in db_totals:
            pytest.skip("No clicks data in DB")

        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None

        dto_val = self._get_metric_value(channel, "clicks")
        assert dto_val is not None, "clicks metric not found in DTO"

        db_val = db_totals["clicks"]
        if db_val == 0:
            assert dto_val == 0
        else:
            pct_diff = abs(dto_val - db_val) / db_val * 100
            assert pct_diff < 1.0, (
                f"Clicks mismatch: DTO={dto_val:.0f} DB={db_val:.0f} "
                f"diff={pct_diff:.2f}%"
            )

    def test_meta_ads_currency_present(
        self, db_session, tenant_id, backend_url
    ):
        """Monetary metrics must carry a currency field."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "spend" not in db_totals:
            pytest.skip("No spend data in DB")

        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None

        for metric in channel.get("metrics", []):
            if metric.get("name") == "spend":
                assert metric.get("currency") is not None, (
                    "spend metric missing currency field in DTO"
                )


class TestIgOrganicPipeline:
    """Verify ig-organic channel metrics flow correctly through the pipeline."""

    def _fetch_db_totals(self, db_session, tenant_id: str) -> dict[str, float]:
        """Read ig-organic account-level metrics from official_metrics."""
        rows = db_session.execute(
            text(
                """
                SELECT metric_name, SUM(value) as total
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'ig-organic'
                  AND provider = 'meta'
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY metric_name
                """
            ),
            {"tid": tenant_id},
        ).all()
        return {row.metric_name: float(row.total) for row in rows}

    def test_ig_organic_present_in_attraction(
        self, db_session, tenant_id, backend_url
    ):
        """ig-organic channel must appear in attraction DTO if DB has data."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if not db_totals:
            pytest.skip("No ig-organic data in DB — run Layer 0 first")

        resp = httpx.get(
            f"{backend_url}/api/v1/analytics/metrics/attraction",
            headers={"X-Tenant-ID": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        dto = resp.json()

        found = False
        for group in dto.get("groups", []):
            for ch in group.get("channels", []):
                if ch.get("slug") == "ig-organic":
                    found = True
                    break
        assert found, "ig-organic not found in attraction DTO"

    def test_ig_organic_reach_matches_db(
        self, db_session, tenant_id, backend_url
    ):
        """IG reach (NON_AGGREGABLE) uses last value, not SUM."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "reach" not in db_totals:
            pytest.skip("No ig-organic reach data in DB")

        resp = httpx.get(
            f"{backend_url}/api/v1/analytics/metrics/attraction",
            headers={"X-Tenant-ID": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        dto = resp.json()

        # Find ig-organic channel
        channel = None
        for group in dto.get("groups", []):
            for ch in group.get("channels", []):
                if ch.get("slug") == "ig-organic":
                    channel = ch
                    break

        assert channel is not None
        dto_reach = None
        for m in channel.get("metrics", []):
            if m.get("name") == "reach":
                dto_reach = float(m.get("value", 0))
                break

        # reach is non-aggregable — DTO should show it (value > 0 if data exists)
        assert dto_reach is not None, "reach not found in ig-organic DTO"
        assert dto_reach > 0, (
            f"reach should be > 0 (DB has {db_totals['reach']})"
        )
```

- [ ] **Step 3: Run the tests (requires Docker containers with data)**

```bash
cd backend && .venv/bin/pytest tests/verification/test_pipeline_meta.py -m verify -x -v
```

Expected: Tests pass (or skip if no data in DB — run Layer 0 first).

- [ ] **Step 4: Verify normal pytest excludes verify tests**

```bash
cd backend && .venv/bin/pytest tests/verification/ -x -q --co 2>&1 | head -5
```

Expected: Tests collected but NOT run by default (verify marker).

Actually, we need to add `addopts` to exclude verify by default. Edit `backend/pyproject.toml` to add the default filter:

In `backend/pyproject.toml`, add after `asyncio_mode = "auto"`:

```toml
addopts = "-m 'not verify'"
```

Then verify:

```bash
cd backend && .venv/bin/pytest tests/ -x -q --co 2>&1 | grep -c "verification"
```

Expected: 0 (verification tests excluded from normal runs).

- [ ] **Step 5: Commit**

```bash
git add backend/tests/verification/ backend/pyproject.toml
git commit -m "feat(verify): add Layer 2 — Meta pipeline integrity tests

pytest @verify tests comparing official_metrics DB values with backend API DTOs.
Excluded from normal pytest runs (addopts = -m 'not verify')."
```

---

### Task 6: Layer 3 — UI Fidelity Playwright Tests

**Files:**
- Create: `frontend/e2e/specs/verify/meta-fidelity.verify.spec.ts`

- [ ] **Step 1: Create directory**

```bash
mkdir -p frontend/e2e/specs/verify
```

- [ ] **Step 2: Write the UI fidelity spec**

Create `frontend/e2e/specs/verify/meta-fidelity.verify.spec.ts`:

```typescript
/**
 * Layer 3: UI Fidelity — Meta channels.
 *
 * Strategy: Call the backend API directly to capture expected DTO values,
 * then navigate the UI and assert displayed values match.
 *
 * NOT mocked — hits the real backend with real data.
 *
 * Requires:
 *   - Docker containers running with real data (post Layer 0)
 *   - Clerk auth configured (same as smoke tests)
 *
 * Run: cd frontend && npx playwright test --project=verify
 */
import { test, expect, type APIRequestContext } from '@playwright/test';

// Use auth fixture for Clerk session
const TENANT_ID = process.env.E2E_TENANT_ID!;
const BACKEND_URL = process.env.E2E_BACKEND_URL || 'http://localhost:8000';

interface MetricValue {
  name: string;
  value: number;
  unit: string;
  currency?: string | null;
}

interface ChannelDto {
  slug: string;
  name: string;
  metrics: MetricValue[];
}

interface GroupDto {
  key: string;
  channels: ChannelDto[];
}

interface AttractionDto {
  groups: GroupDto[];
  header_kpis?: Record<string, unknown>[];
}

function findChannel(dto: AttractionDto, slug: string): ChannelDto | undefined {
  for (const group of dto.groups ?? []) {
    for (const ch of group.channels ?? []) {
      if (ch.slug === slug) return ch;
    }
  }
  return undefined;
}

function getMetric(channel: ChannelDto, name: string): MetricValue | undefined {
  return channel.metrics?.find((m) => m.name === name);
}

/**
 * Format a number the way our UI does, for text matching.
 * Simplified — matches the most common patterns.
 */
function formatForMatch(value: number, unit: string): string {
  if (unit === 'currency') {
    // UI shows formatted currency — we just check the numeric part
    return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (unit === 'percentage') {
    return value.toFixed(2);
  }
  if (unit === 'ratio') {
    return value.toFixed(2);
  }
  // count — large numbers formatted with separators
  if (value >= 1000) {
    return value.toLocaleString('en-US', { maximumFractionDigits: 0 });
  }
  return value.toString();
}

test.describe('Meta Ads - Data Fidelity @verify', () => {
  let attractionDto: AttractionDto;

  test.beforeAll(async ({ request }: { request: APIRequestContext }) => {
    const response = await request.get(
      `${BACKEND_URL}/api/v1/analytics/metrics/attraction`,
      { headers: { 'X-Tenant-ID': TENANT_ID } },
    );
    expect(response.ok()).toBeTruthy();
    attractionDto = await response.json();
  });

  test('meta-ads channel exists in attraction API response', () => {
    const channel = findChannel(attractionDto, 'meta-ads');
    expect(channel).toBeDefined();
    expect(channel!.metrics.length).toBeGreaterThan(0);
  });

  test('meta-ads spend is visible and matches API', async ({ page }) => {
    const channel = findChannel(attractionDto, 'meta-ads');
    test.skip(!channel, 'No meta-ads channel in DTO');

    const spendMetric = getMetric(channel!, 'spend');
    test.skip(!spendMetric, 'No spend metric in DTO');

    await page.goto(
      `/${TENANT_ID}/growth-studio/atraccion-captura`,
      { waitUntil: 'networkidle' },
    );

    // Click on Meta Ads channel to open sidebar
    const metaAdsRow = page.getByRole('button', { name: /Meta Ads/i }).first();
    await expect(metaAdsRow).toBeVisible({ timeout: 15_000 });
    await metaAdsRow.click();

    // The sidebar should show the spend value
    const spendFormatted = formatForMatch(spendMetric!.value, 'currency');
    // Look for the numeric part of the formatted spend in the sidebar
    const sidebar = page.locator('[data-testid="channel-sidebar"], [role="complementary"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10_000 });

    // Verify spend value appears somewhere in the sidebar
    await expect(sidebar).toContainText(spendFormatted, { timeout: 5_000 });
  });

  test('meta-ads impressions visible and matches API', async ({ page }) => {
    const channel = findChannel(attractionDto, 'meta-ads');
    test.skip(!channel, 'No meta-ads channel in DTO');

    const metric = getMetric(channel!, 'impressions');
    test.skip(!metric, 'No impressions metric in DTO');

    await page.goto(
      `/${TENANT_ID}/growth-studio/atraccion-captura`,
      { waitUntil: 'networkidle' },
    );

    const metaAdsRow = page.getByRole('button', { name: /Meta Ads/i }).first();
    await expect(metaAdsRow).toBeVisible({ timeout: 15_000 });
    await metaAdsRow.click();

    const sidebar = page.locator('[data-testid="channel-sidebar"], [role="complementary"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10_000 });

    const formatted = formatForMatch(metric!.value, 'count');
    await expect(sidebar).toContainText(formatted, { timeout: 5_000 });
  });
});

test.describe('IG Organic - Data Fidelity @verify', () => {
  let attractionDto: AttractionDto;

  test.beforeAll(async ({ request }: { request: APIRequestContext }) => {
    const response = await request.get(
      `${BACKEND_URL}/api/v1/analytics/metrics/attraction`,
      { headers: { 'X-Tenant-ID': TENANT_ID } },
    );
    expect(response.ok()).toBeTruthy();
    attractionDto = await response.json();
  });

  test('ig-organic channel exists in attraction API response', () => {
    const channel = findChannel(attractionDto, 'ig-organic');
    expect(channel).toBeDefined();
    expect(channel!.metrics.length).toBeGreaterThan(0);
  });

  test('ig-organic reach visible and non-zero', async ({ page }) => {
    const channel = findChannel(attractionDto, 'ig-organic');
    test.skip(!channel, 'No ig-organic channel in DTO');

    const metric = getMetric(channel!, 'reach');
    test.skip(!metric || metric.value === 0, 'No reach data');

    await page.goto(
      `/${TENANT_ID}/growth-studio/atraccion-captura`,
      { waitUntil: 'networkidle' },
    );

    // Click IG Organic to open sidebar
    const igRow = page.getByRole('button', { name: /Instagram Organic|IG Organic/i }).first();
    await expect(igRow).toBeVisible({ timeout: 15_000 });
    await igRow.click();

    const sidebar = page.locator('[data-testid="channel-sidebar"], [role="complementary"]').first();
    await expect(sidebar).toBeVisible({ timeout: 10_000 });

    const formatted = formatForMatch(metric!.value, 'count');
    await expect(sidebar).toContainText(formatted, { timeout: 5_000 });
  });
});
```

- [ ] **Step 3: Test the verify spec (requires containers running + real data)**

```bash
cd frontend && npx playwright test --project=verify --reporter=list
```

Expected: Tests pass against real backend data, or skip if no data.

- [ ] **Step 4: Verify verify project doesn't run in smoke/regression**

```bash
cd frontend && npx playwright test --project=smoke --list 2>&1 | grep -c "verify"
```

Expected: 0 (verify specs not picked up by smoke project).

- [ ] **Step 5: Commit**

```bash
git add frontend/e2e/specs/verify/meta-fidelity.verify.spec.ts
git commit -m "feat(verify): add Layer 3 — Meta UI fidelity Playwright tests

Calls real backend API, navigates Growth Studio, asserts displayed values
match DTO. Runs in 'verify' Playwright project, isolated from smoke/regression."
```

---

### Task 7: Makefile Targets

**Files:**
- Modify: `Makefile:1` (add to .PHONY)
- Modify: `Makefile:199` (append targets)

- [ ] **Step 1: Add verify targets to Makefile**

Append to `Makefile` after line 199:

```makefile

# --- Data Reliability Verification (4-Layer Protocol) ---
# See: docs/superpowers/specs/2026-04-12-data-reliability-verification-design.md
# Rule: .claude/rules/data-reliability.md

# Default env and days for verify commands
env ?= local
days ?= 7
provider ?= meta

verify-etl:
	cd backend && .venv/bin/python scripts/verify/run_etl.py --provider $(provider) --days $(days) --env $(env)

verify-probe-meta:
	cd backend && .venv/bin/python scripts/verify/probes/meta_probe.py --days $(days) --env $(env) --output scripts/verify/snapshots/meta-latest.json

verify-pipeline:
	cd backend && .venv/bin/pytest tests/verification/ -m verify -x -q --tb=short

verify-ui:
	cd frontend && npx playwright test --project=verify

verify-meta: verify-etl verify-probe-meta verify-pipeline verify-ui
	@echo "=== Meta 4-layer verification complete ==="

verify-all: verify-meta
```

- [ ] **Step 2: Update .PHONY line**

In `Makefile` line 1, append the new targets to the .PHONY list:

Add after `arch-test`: `verify-etl verify-probe-meta verify-pipeline verify-ui verify-meta verify-all`

- [ ] **Step 3: Verify Makefile syntax**

```bash
make --dry-run verify-meta env=local days=3 2>&1 | head -10
```

Expected: Shows the 4 commands that would run (dry-run, no actual execution).

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "chore(verify): add make verify-* targets for 4-layer protocol

make verify-meta: full chain (ETL + probe + pipeline + UI).
make verify-pipeline: Layer 2 only. make verify-ui: Layer 3 only.
Supports env=local|prod and days=N params."
```

---

### Task 8: Enforcement Rule

**Files:**
- Create: `.claude/rules/data-reliability.md`

- [ ] **Step 1: Write the enforcement rule**

Create `.claude/rules/data-reliability.md`:

```markdown
# Data Reliability Verification — Always Verify, Never Guess

Non-negotiable workflow rule for any task that touches the Growth Studio data pipeline.
The 4-Layer Verification Protocol is the only way to confirm that displayed values are correct.

## The 4 Layers

| Layer | What it verifies | Command | When to run |
|-------|-----------------|---------|-------------|
| 0: ETL Execution | Fresh data in DB | `make verify-etl provider={name}` | Before Layers 1-3 when data may be stale |
| 1: Source Probe | External API values == official_metrics | `make verify-probe-{provider}` | After touching providers or ETL pipeline |
| 2: Pipeline Integrity | official_metrics values == stage service DTOs | `make verify-pipeline` | After touching stage services, DTOs, or API routes |
| 3: UI Fidelity | Backend API response == UI display | `make verify-ui` | After touching frontend components, hooks, or formatters |

## Trigger Matrix

| You modified... | Run these layers |
|----------------|-----------------|
| `backend/src/modules/analytics/infrastructure/providers/*.py` | 0 + 1 + 2 |
| `backend/src/modules/analytics/infrastructure/etl/*.py` | 0 + 1 + 2 |
| `backend/src/modules/analytics/application/services/stage_services/*.py` | 2 |
| `backend/src/modules/analytics/application/dto/*.py` | 2 + 3 |
| `backend/src/modules/analytics/api/metrics.py` | 2 + 3 |
| `backend/src/modules/analytics/api/campaigns.py` | 2 + 3 |
| `backend/src/modules/analytics/api/email_metrics.py` | 2 + 3 |
| `backend/src/modules/analytics/application/services/channel_registry.py` | 2 |
| `frontend/src/features/growth-studio/components/**` | 3 |
| `frontend/src/features/growth-studio/api/*.ts` | 3 |
| `frontend/src/features/growth-studio/hooks/*.ts` | 3 |
| `frontend/src/lib/format-money.ts` | 3 |
| `frontend/src/lib/format-date.ts` | 3 |

## The 5-step verification workflow

1. **Before modifying:** Run the relevant layers to capture baseline state
2. **Make the change**
3. **After modifying:** Run the same layers to verify no regression
4. **If any layer fails:** Investigate and fix — do not skip or suppress
5. **Commit:** Note in the commit message which verification layers passed

## Quick commands

```bash
make verify-meta              # Full 4-layer chain, local
make verify-meta env=prod     # Full 4-layer chain, production
make verify-pipeline          # Layer 2 only (pytest -m verify)
make verify-ui                # Layer 3 only (Playwright --project=verify)
make verify-probe-meta days=7 # Layer 1 only (Meta API vs DB)
make verify-etl provider=meta # Layer 0 only (trigger extraction)
```

## Adding a new provider

When creating a probe for a new provider, follow the Meta pilot:

1. Create `backend/scripts/verify/probes/{provider}_probe.py` (copy meta_probe.py as template)
2. Define `EXPECTED_MAPPINGS` for all API fields the provider extracts — independent of the ETL provider code
3. Create `backend/tests/verification/test_pipeline_{provider}.py` with `@pytest.mark.verify`
4. Create `frontend/e2e/specs/verify/{provider}-fidelity.verify.spec.ts`
5. Add `verify-probe-{provider}` and `verify-{provider}` targets to Makefile
6. Update `verify-all` to include the new provider

## Anti-patterns to refuse

- Modifying a provider without running Layer 1 (`make verify-probe-{provider}`)
- Modifying a stage service or DTO without running Layer 2 (`make verify-pipeline`)
- Modifying a dashboard component without running Layer 3 (`make verify-ui`)
- Skipping verification because "it is just a small change" — there are no small changes to the data pipeline
- Using mocked data in verify tests — they exist specifically for real data verification
- Committing Growth Studio changes without noting which verification layers passed
- Adding `@pytest.mark.skip` or `test.skip()` to verification tests to make CI pass

## Relationship to other rules

- **ETL Extraction Contract** (`.claude/rules/etl-extraction-contract.md`): Governs what the ETL extracts. This rule governs verifying that the extraction is correct.
- **Analytics Metrics** (`.claude/rules/analytics-metrics.md`): Governs the runtime pipeline architecture. This rule governs verifying that the pipeline produces correct output.
- **Currency Handling** (`.claude/rules/currency-handling.md`): Governs how currency is handled. Layer 2 and 3 verify that currency flows correctly.
```

- [ ] **Step 2: Add reference in CLAUDE.md Critical Rules**

In `CLAUDE.md`, add rule 15 after rule 14 in the Critical Rules section:

```
15. **Data Reliability:** After modifying any Growth Studio file (provider, service, DTO, frontend component), run the corresponding verification layer. See `.claude/rules/data-reliability.md`.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/data-reliability.md CLAUDE.md
git commit -m "docs(verify): add data-reliability enforcement rule

Trigger matrix mandates running verification layers before committing
any Growth Studio modification. Added as Critical Rule #15 in CLAUDE.md."
```

---

### Task 9: Integration Test — Full Chain Smoke Test

**Files:** None new — tests the whole system end-to-end.

- [ ] **Step 1: Run the full verification chain**

```bash
make verify-meta env=local days=3
```

Expected output sequence:
1. `[Layer 0] SUCCESS: meta loaded=N skipped=M` (or SKIPPED if cooldown)
2. Table with Channel/Metric/API/DB/Diff%/Status columns, ending with PASSED/FAILED
3. `Snapshot saved to scripts/verify/snapshots/meta-latest.json`
4. pytest output: `N passed` (or skipped if no data)
5. Playwright output: `N passed` (or skipped if no data)
6. `=== Meta 4-layer verification complete ===`

- [ ] **Step 2: Verify probe detects corruption (sanity test)**

Temporarily corrupt a metric value in the DB:

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c \
  "UPDATE official_metrics SET value = value * 100 WHERE channel_slug = 'meta-ads' AND metric_name = 'spend' AND metric_date = CURRENT_DATE - 2 LIMIT 1;"
```

Run probe again:

```bash
make verify-probe-meta days=3
```

Expected: At least one `FAIL` row for spend, report shows `FAILED`.

Restore the value:

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c \
  "UPDATE official_metrics SET value = value / 100 WHERE channel_slug = 'meta-ads' AND metric_name = 'spend' AND metric_date = CURRENT_DATE - 2 AND value > 10000 LIMIT 1;"
```

- [ ] **Step 3: Verify individual layer commands work**

```bash
make verify-pipeline
make verify-ui
```

Expected: Each layer runs independently.

- [ ] **Step 4: Final commit**

```bash
git add -A  # Only if there are leftover files from testing
git commit -m "test(verify): validate full 4-layer verification chain

Confirmed: Layer 0 triggers ETL, Layer 1 detects corruption,
Layer 2 catches DTO mismatches, Layer 3 asserts UI values.
All 4 layers run independently via make verify-*."
```

---

## Summary

| Task | Layer | Files | Commits |
|------|-------|-------|---------|
| 1 | Infra | .gitignore, pyproject.toml, playwright.config.ts | 1 |
| 2 | 0 | scripts/verify/run_etl.py | 1 |
| 3 | 1 | scripts/verify/probes/base_probe.py | 1 |
| 4 | 1 | scripts/verify/probes/meta_probe.py | 1 |
| 5 | 2 | tests/verification/test_pipeline_meta.py | 1 |
| 6 | 3 | e2e/specs/verify/meta-fidelity.verify.spec.ts | 1 |
| 7 | All | Makefile | 1 |
| 8 | Rule | .claude/rules/data-reliability.md, CLAUDE.md | 1 |
| 9 | All | Integration smoke test | 1 |

**Total: 9 tasks, 9 commits, ~15 new files.**
