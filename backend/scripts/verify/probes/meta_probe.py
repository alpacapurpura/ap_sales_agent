"""Layer 1 — Meta Source Probe.

Independently calls Meta Graph API (ads, ig-organic, fb-organic) and
compares results with official_metrics.  Shares NO code with
meta_provider.py — every mapping and API call is defined here so the
probe stays an honest second opinion.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from uuid import UUID

import httpx

# ---------------------------------------------------------------------------
# Path manipulation so the script is importable both natively (from backend/)
# and inside the Docker container (where /app == backend/).
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from scripts.verify.probes.base_probe import ProbeReport, ProbeResult
from src.core.config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"
THRESHOLD_PCT = 1.0

# ---------------------------------------------------------------------------
# Expected mappings — intentionally independent from meta_provider.py
# ---------------------------------------------------------------------------

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

META_ADS_ACTION_MAP: dict[str, str] = {
    "offsite_conversion.fb_pixel_purchase": "conversions",
    "onsite_conversion.purchase": "conversions",
    "offsite_conversion.fb_pixel_lead": "meta_leads",
    "lead": "meta_leads",
    "link_click": "meta_link_clicks",
    "landing_page_view": "meta_landing_page_views",
    "video_view": "meta_video_views",
}

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

FB_ORGANIC_METRICS: dict[str, str] = {
    "page_impressions_organic_unique": "fb_page_reach",
    "page_post_engagements": "fb_page_engagement",
}

# Fields requested from Meta Ads Insights API
_ADS_FIELDS = (
    "reach,impressions,clicks,spend,ctr,cpm,cpc,cpp,frequency,"
    "inline_link_clicks,inline_post_engagement,"
    "cost_per_inline_link_click,actions,action_values,"
    "outbound_clicks,purchase_roas,cost_per_action_type,"
    "cost_per_outbound_click"
)

# IG breakdownable metrics (can use media_product_type breakdown)
_IG_BREAKDOWNABLE = (
    "reach,views,total_interactions,likes,comments,shares,saves,accounts_engaged,profile_links_taps,replies,reposts"
)

# IG non-breakdownable (no breakdown allowed)
_IG_NON_BREAKDOWNABLE = "reach"  # placeholder; we use breakdownable for most

_IG_MAX_DAYS = 30  # Meta enforces <=30 days per /insights call


# ---------------------------------------------------------------------------
# Credential resolution
# ---------------------------------------------------------------------------


def get_credentials_from_db(
    env: str,
    tenant_id: UUID,
) -> dict:
    """Read channel_connections credentials for Meta channels.

    Uses the ORM model so EncryptedJSON automatically decrypts the
    credentials column via Fernet.  Raw SQL would return the encrypted
    blob, which is why we import the model here.
    """
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )
    from src.shared.infrastructure import model_registry  # noqa: F401

    db_url = settings.DATABASE_URL
    engine = create_engine(db_url)

    with Session(engine) as session:
        stmt = (
            select(ChannelConnectionModel)
            .where(
                ChannelConnectionModel.tenant_id == tenant_id,
                ChannelConnectionModel.channel_type == "meta",
                ChannelConnectionModel.is_active.is_(True),
                ChannelConnectionModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        conn = session.execute(stmt).scalar_one_or_none()
        if conn is None:
            return {}
        merged = {}
        if conn.credentials:
            merged.update(conn.credentials)
        if conn.config:
            merged.update(conn.config)

    engine.dispose()
    return merged


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_organic_from_breakdown(item: dict) -> float:
    """Sum total_value results excluding AD media_product_type."""
    total_value = item.get("total_value", {})
    breakdowns = total_value.get("breakdowns", [])
    if not breakdowns:
        return float(total_value.get("value", 0))
    total = 0.0
    for bd in breakdowns:
        for result in bd.get("results", []):
            dims = {d.get("dimension_key"): d.get("dimension_value") for d in result.get("dimension_values", [])}
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
            dims = {d.get("dimension_key"): d.get("dimension_value") for d in result.get("dimension_values", [])}
            val = float(result.get("value", 0))
            ft = dims.get("follow_type", "")
            if ft in ("gained", "follow"):
                gained += val
            elif ft in ("lost", "unfollow"):
                lost += val
    return gained, lost


def _paginate(
    client: httpx.Client,
    url: str,
    params: dict,
) -> list[dict]:
    """Follow Meta paging.next links until exhausted."""
    all_data: list[dict] = []
    resp = client.get(url, params=params, timeout=60)
    resp.raise_for_status()
    body = resp.json()
    all_data.extend(body.get("data", []))

    next_url = body.get("paging", {}).get("next")
    while next_url:
        resp = client.get(next_url, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        all_data.extend(body.get("data", []))
        next_url = body.get("paging", {}).get("next")

    return all_data


# ---------------------------------------------------------------------------
# API Callers
# ---------------------------------------------------------------------------


def probe_meta_ads(
    access_token: str,
    ad_account_id: str,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Call Meta Ads Insights API independently. Returns {(date, metric_name): value}."""
    results: dict[tuple[date, str], float] = {}

    # Normalise ad_account_id — ensure it has the act_ prefix
    acct = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"

    url = f"{GRAPH_API_BASE}/{acct}/insights"
    params = {
        "access_token": access_token,
        "fields": _ADS_FIELDS,
        "time_range": f'{{"since":"{start_date.isoformat()}","until":"{end_date.isoformat()}"}}',
        "time_increment": "1",
        "level": "account",
        "limit": "500",
    }

    with httpx.Client() as client:
        rows = _paginate(client, url, params)

    for row in rows:
        row_date_str = row.get("date_start", "")
        if not row_date_str:
            continue
        row_date = date.fromisoformat(row_date_str)

        # Simple fields
        for api_field, metric_name in META_ADS_SIMPLE_FIELDS.items():
            raw_val = row.get(api_field)
            if raw_val is not None:
                key = (row_date, metric_name)
                results[key] = results.get(key, 0.0) + float(raw_val)

        # Actions
        for action in row.get("actions", []):
            action_type = action.get("action_type", "")
            metric_name = META_ADS_ACTION_MAP.get(action_type)
            if metric_name:
                key = (row_date, metric_name)
                results[key] = results.get(key, 0.0) + float(action.get("value", 0))

        # Action values (purchase ROAS source)
        for av in row.get("action_values", []):
            action_type = av.get("action_type", "")
            if action_type in (
                "offsite_conversion.fb_pixel_purchase",
                "onsite_conversion.purchase",
            ):
                key = (row_date, "meta_purchase_value")
                results[key] = results.get(key, 0.0) + float(av.get("value", 0))

        # Outbound clicks
        for oc in row.get("outbound_clicks", []):
            if oc.get("action_type") == "outbound_click":
                key = (row_date, "meta_outbound_clicks")
                results[key] = results.get(key, 0.0) + float(oc.get("value", 0))

        # Purchase ROAS
        for roas in row.get("purchase_roas", []):
            if roas.get("action_type") in (
                "offsite_conversion.fb_pixel_purchase",
                "omni_purchase",
            ):
                key = (row_date, "meta_roas")
                results[key] = results.get(key, 0.0) + float(roas.get("value", 0))

        # Cost per action type
        for cpa in row.get("cost_per_action_type", []):
            action_type = cpa.get("action_type", "")
            if action_type in (
                "offsite_conversion.fb_pixel_purchase",
                "onsite_conversion.purchase",
            ):
                key = (row_date, "meta_cost_per_purchase")
                results[key] = results.get(key, 0.0) + float(cpa.get("value", 0))

        # Cost per outbound click
        for cpoc in row.get("cost_per_outbound_click", []):
            if cpoc.get("action_type") == "outbound_click":
                key = (row_date, "meta_cost_per_outbound_click")
                results[key] = results.get(key, 0.0) + float(cpoc.get("value", 0))

    return results


def probe_ig_organic(
    access_token: str,
    ig_user_id: str,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Call IG Insights API independently. Returns {(date, metric_name): value}."""
    results: dict[tuple[date, str], float] = {}

    with httpx.Client() as client:
        # Split into <=30-day chunks
        chunk_start = start_date
        while chunk_start <= end_date:
            chunk_end = min(chunk_start + timedelta(days=_IG_MAX_DAYS - 1), end_date)

            since_ts = int(datetime.combine(chunk_start, datetime.min.time()).timestamp())
            until_ts = int(datetime.combine(chunk_end + timedelta(days=1), datetime.min.time()).timestamp())

            # 1) Breakdownable metrics with media_product_type breakdown
            url = f"{GRAPH_API_BASE}/{ig_user_id}/insights"
            params = {
                "access_token": access_token,
                "metric": _IG_BREAKDOWNABLE,
                "period": "day",
                "since": str(since_ts),
                "until": str(until_ts),
                "metric_type": "total_value",
                "breakdown": "media_product_type",
            }
            resp = client.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                for item in resp.json().get("data", []):
                    api_metric = item.get("name", "")
                    our_metric = IG_ORGANIC_METRICS.get(api_metric)
                    if not our_metric:
                        continue
                    value = _extract_organic_from_breakdown(item)
                    key = (chunk_end, our_metric)
                    results[key] = results.get(key, 0.0) + value

            # 2) Follows and unfollows with follow_type breakdown
            params_follows = {
                "access_token": access_token,
                "metric": "follows_and_unfollows",
                "period": "day",
                "since": str(since_ts),
                "until": str(until_ts),
                "metric_type": "total_value",
                "breakdown": "follow_type",
            }
            resp = client.get(url, params=params_follows, timeout=60)
            if resp.status_code == 200:
                for item in resp.json().get("data", []):
                    if item.get("name") == "follows_and_unfollows":
                        gained, lost = _parse_follow_type(item)
                        results[(chunk_end, "ig_follows_gained")] = (
                            results.get((chunk_end, "ig_follows_gained"), 0.0) + gained
                        )
                        results[(chunk_end, "ig_follows_lost")] = (
                            results.get((chunk_end, "ig_follows_lost"), 0.0) + lost
                        )
                        results[(chunk_end, "ig_net_followers")] = (
                            results.get((chunk_end, "ig_net_followers"), 0.0) + gained - lost
                        )

            chunk_start = chunk_end + timedelta(days=1)

        # 3) User node: followers_count, media_count (snapshot, not time-series)
        user_url = f"{GRAPH_API_BASE}/{ig_user_id}"
        user_params = {
            "access_token": access_token,
            "fields": "followers_count,media_count",
        }
        resp = client.get(user_url, params=user_params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "followers_count" in data:
                results[(end_date, "ig_followers_count")] = float(data["followers_count"])
            if "media_count" in data:
                results[(end_date, "ig_media_count")] = float(data["media_count"])

    return results


def probe_fb_organic(
    access_token: str,
    page_id: str,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Call FB Page Insights API independently. Returns {(date, metric_name): value}."""
    results: dict[tuple[date, str], float] = {}

    url = f"{GRAPH_API_BASE}/{page_id}/insights"
    metrics = ",".join(FB_ORGANIC_METRICS.keys())
    params = {
        "access_token": access_token,
        "metric": metrics,
        "period": "day",
        "since": start_date.isoformat(),
        "until": (end_date + timedelta(days=1)).isoformat(),
    }

    with httpx.Client() as client:
        resp = client.get(url, params=params, timeout=60)
        if resp.status_code != 200:
            return results

        for item in resp.json().get("data", []):
            api_metric = item.get("name", "")
            our_metric = FB_ORGANIC_METRICS.get(api_metric)
            if not our_metric:
                continue
            for point in item.get("values", []):
                end_time = point.get("end_time", "")
                if not end_time:
                    continue
                # end_time is ISO datetime; extract date
                point_date = date.fromisoformat(end_time[:10])
                if start_date <= point_date <= end_date:
                    val = float(point.get("value", 0))
                    key = (point_date, our_metric)
                    results[key] = results.get(key, 0.0) + val

    return results


# ---------------------------------------------------------------------------
# DB comparison
# ---------------------------------------------------------------------------


def fetch_db_metrics(
    tenant_id: UUID,
    provider: str,
    channel_slug: str,
    start_date: date,
    end_date: date,
) -> dict[tuple[date, str], float]:
    """Read official_metrics for comparison. Account-level only."""
    from sqlalchemy import create_engine, text

    db_url = settings.DATABASE_URL
    engine = create_engine(db_url)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT metric_date, metric_name, SUM(value) as total "
                "FROM official_metrics "
                "WHERE tenant_id = :tid "
                "  AND provider = :provider "
                "  AND channel_slug = :channel "
                "  AND metric_date BETWEEN :start AND :end "
                "  AND campaign_id IS NULL "
                "  AND ad_set_id IS NULL "
                "  AND ad_id IS NULL "
                "GROUP BY metric_date, metric_name"
            ),
            {
                "tid": str(tenant_id),
                "provider": provider,
                "channel": channel_slug,
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        ).fetchall()

    engine.dispose()

    db_data: dict[tuple[date, str], float] = {}
    for row in rows:
        metric_date = row[0] if isinstance(row[0], date) else date.fromisoformat(str(row[0]))
        db_data[(metric_date, row[1])] = float(row[2])
    return db_data


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_meta_probe(
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    env: str = "local",
    threshold_pct: float = THRESHOLD_PCT,
) -> ProbeReport:
    """Run all Meta channel probes and produce a unified report."""
    report = ProbeReport(
        provider="meta",
        tenant_id=tenant_id,
        probe_date=date.today(),
        date_range=(start_date, end_date),
        env=env,
        threshold_pct=threshold_pct,
    )

    creds = get_credentials_from_db(env, tenant_id)
    access_token = creds.get("access_token", "")
    if not access_token:
        print("[META PROBE] No access_token found — skipping all Meta channels.")
        return report

    # --- Meta Ads ---
    ad_account_id = creds.get("ad_account_id", "")
    if ad_account_id:
        print(f"[META PROBE] Probing meta-ads for account {ad_account_id} ...")
        api_data = probe_meta_ads(access_token, ad_account_id, start_date, end_date)
        db_data = fetch_db_metrics(tenant_id, "meta", "meta-ads", start_date, end_date)

        all_keys = set(api_data.keys()) | set(db_data.keys())
        for key in sorted(all_keys):
            d, metric = key
            report.results.append(
                ProbeResult.compare(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name=metric,
                    metric_date=d,
                    api_value=api_data.get(key, 0.0),
                    db_value=db_data.get(key),
                    threshold_pct=threshold_pct,
                )
            )
    else:
        print("[META PROBE] No ad_account_id — skipping meta-ads.")

    # --- IG Organic ---
    ig_user_id = creds.get("ig_user_id", "") or creds.get("instagram_business_account_id", "")
    if ig_user_id:
        print(f"[META PROBE] Probing ig-organic for user {ig_user_id} ...")
        api_data = probe_ig_organic(access_token, ig_user_id, start_date, end_date)
        db_data = fetch_db_metrics(tenant_id, "meta", "ig-organic", start_date, end_date)

        all_keys = set(api_data.keys()) | set(db_data.keys())
        for key in sorted(all_keys):
            d, metric = key
            report.results.append(
                ProbeResult.compare(
                    provider="meta",
                    channel_slug="ig-organic",
                    metric_name=metric,
                    metric_date=d,
                    api_value=api_data.get(key, 0.0),
                    db_value=db_data.get(key),
                    threshold_pct=threshold_pct,
                )
            )
    else:
        print("[META PROBE] No ig_user_id — skipping ig-organic.")

    # --- FB Organic ---
    page_id = creds.get("page_id", "") or creds.get("facebook_page_id", "")
    if page_id:
        print(f"[META PROBE] Probing fb-organic for page {page_id} ...")
        api_data = probe_fb_organic(access_token, page_id, start_date, end_date)
        db_data = fetch_db_metrics(tenant_id, "meta", "fb-organic", start_date, end_date)

        all_keys = set(api_data.keys()) | set(db_data.keys())
        for key in sorted(all_keys):
            d, metric = key
            report.results.append(
                ProbeResult.compare(
                    provider="meta",
                    channel_slug="fb-organic",
                    metric_name=metric,
                    metric_date=d,
                    api_value=api_data.get(key, 0.0),
                    db_value=db_data.get(key),
                    threshold_pct=threshold_pct,
                )
            )
    else:
        print("[META PROBE] No page_id — skipping fb-organic.")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Layer 1 — Meta Source Probe: compare Graph API with official_metrics")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to probe (default: 7)",
    )
    parser.add_argument(
        "--env",
        choices=["local", "prod"],
        default="local",
        help="Environment (default: local)",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=None,
        help="Tenant UUID (falls back to VERIFY_TENANT_ID / E2E_TENANT_ID env vars)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save JSON snapshot (optional)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=THRESHOLD_PCT,
        help=f"Match threshold percentage (default: {THRESHOLD_PCT})",
    )

    args = parser.parse_args()

    # Resolve tenant ID
    tid_str = args.tenant_id or os.environ.get("VERIFY_TENANT_ID") or os.environ.get("E2E_TENANT_ID")
    if not tid_str:
        print("ERROR: --tenant-id or VERIFY_TENANT_ID / E2E_TENANT_ID env var required.")
        sys.exit(1)

    tenant_id = UUID(tid_str)
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=args.days - 1)

    print(f"Meta Source Probe | {args.env} | tenant={tenant_id}")
    print(f"Date range: {start_date} → {end_date} ({args.days} days)")
    print(f"Threshold: {args.threshold}%")
    print("=" * 97)

    report = run_meta_probe(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        env=args.env,
        threshold_pct=args.threshold,
    )

    print(report.to_table())

    if args.output:
        with open(args.output, "w") as f:
            f.write(report.to_json())
        print(f"\nSnapshot saved to {args.output}")

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
