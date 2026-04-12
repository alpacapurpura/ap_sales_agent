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

import httpx

# Resolve tenant from env — same var Playwright uses
TENANT_ID = os.environ.get("VERIFY_TENANT_ID") or os.environ.get("E2E_TENANT_ID")

ENV_URLS = {
    "local": "http://localhost:8000",
    "prod": "http://localhost:18000",  # SSH tunnel
}

TIMEOUT_SECONDS = 300  # 5 minutes max wait


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

    print(
        f"[Layer 0] Triggering ETL for provider={args.provider} days={args.days} env={args.env}"
    )
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
        print(
            f"ERROR: HTTP {exc.response.status_code}: {exc.response.text}",
            file=sys.stderr,
        )
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
    if status == "skipped_cooldown":
        remaining = provider_detail.get("remaining_minutes", "?")
        print(
            f"[Layer 0] SKIPPED: {args.provider} on cooldown ({remaining} min remaining). "
            f"This means a recent extraction already ran — data is fresh.",
        )
        return 0
    error = provider_detail.get("error", "unknown error")
    print(f"[Layer 0] FAILED: {args.provider} — {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
