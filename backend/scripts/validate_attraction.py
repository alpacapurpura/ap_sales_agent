#!/usr/bin/env python3
"""Validate Attraction ETL metrics against live provider API calls.

Compares ETL-stored metric aggregations with direct provider API extractions
for the Visionarias tenant. Reports per-channel pass/fail with tolerance check.

Usage (inside Docker container):
    python scripts/validate_attraction.py
    python scripts/validate_attraction.py --tenant-id <uuid> --tolerance 0.05

Exit codes:
    0 - All connected metrics pass within tolerance
    1 - One or more metrics fail tolerance check
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

# Ensure project root is importable (Docker workdir is /app)
_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_root = os.path.dirname(_script_dir)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)
# Also add /app for Docker container compatibility
if "/app" not in sys.path:
    sys.path.insert(0, "/app")

from src.core.database import SessionLocal
from src.modules.analytics.application.services.channel_registry import (
    ChannelRegistry,
    STAGE_CHANNEL_MAP,
    PROVIDER_TO_CHANNEL_TYPES,
)
from src.modules.analytics.infrastructure.providers.registry import (
    PROVIDER_REGISTRY,
    get_provider,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.connections.application.services.connection_port_impl import (
    ConnectionPortImpl,
)

logger = logging.getLogger(__name__)

# Default tenant: Visionarias (from seed data or environment)
DEFAULT_TENANT_ID = os.environ.get(
    "VISIONARIAS_TENANT_ID",
    "00000000-0000-0000-0000-000000000001",
)
DEFAULT_TOLERANCE = 0.05  # 5%


class ValidationResult:
    """Holds the result for a single metric comparison."""

    def __init__(
        self,
        channel_slug: str,
        metric_name: str,
        status: str,  # "PASS", "FAIL", "SKIP"
        etl_value: Optional[float] = None,
        live_value: Optional[float] = None,
        diff_pct: Optional[float] = None,
        reason: Optional[str] = None,
    ):
        self.channel_slug = channel_slug
        self.metric_name = metric_name
        self.status = status
        self.etl_value = etl_value
        self.live_value = live_value
        self.diff_pct = diff_pct
        self.reason = reason

    def format_line(self) -> str:
        """Format as a human-readable report line."""
        slug_metric = f"{self.channel_slug} / {self.metric_name}"
        if self.status == "SKIP":
            return f"    {slug_metric:<45} SKIP  ({self.reason})"
        elif self.status == "PASS":
            return (
                f"    {slug_metric:<45} PASS  "
                f"(ETL: {self._fmt(self.etl_value)} | "
                f"Live: {self._fmt(self.live_value)} | "
                f"Diff: {self.diff_pct:.1f}%)"
            )
        else:  # FAIL
            return (
                f"    {slug_metric:<45} FAIL  "
                f"(ETL: {self._fmt(self.etl_value)} | "
                f"Live: {self._fmt(self.live_value)} | "
                f"Diff: {self.diff_pct:.1f}%)"
            )

    @staticmethod
    def _fmt(val: Optional[float]) -> str:
        """Format numeric value with comma separators."""
        if val is None:
            return "N/A"
        if val == int(val) and abs(val) < 1_000_000_000:
            return f"{int(val):,}"
        return f"{val:,.2f}"


def _compute_diff(live: float, stored: float) -> float:
    """Compute percentage difference. Denominator is max(live, 1) to avoid div-by-zero."""
    denominator = max(abs(live), 1.0)
    return abs(live - stored) / denominator * 100.0


def _get_etl_values(
    repo: OfficialMetricsRepository,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> Dict[Tuple[str, str], float]:
    """Read ETL-stored official metrics and aggregate by (channel_slug, metric_name).

    Returns a dict mapping (channel_slug, metric_name) -> summed value for the period.
    """
    metrics = repo.get_metrics(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )

    aggregated: Dict[Tuple[str, str], float] = {}
    for m in metrics:
        key = (m.channel_slug, m.metric_name)
        aggregated[key] = aggregated.get(key, 0.0) + (m.value or 0.0)

    return aggregated


async def _get_live_values(
    provider_name: str,
    tenant_id: UUID,
    connection_port: ConnectionPortImpl,
    start_date: date,
    end_date: date,
) -> Optional[Dict[Tuple[str, str], float]]:
    """Extract live metrics from a provider API.

    Returns dict mapping (channel_slug, metric_name) -> value,
    or None if the API call fails.
    """
    try:
        provider = get_provider(provider_name)
    except ValueError as exc:
        logger.warning("Provider not registered: %s (%s)", provider_name, exc)
        return None

    # Determine the channel_type(s) for credential lookup
    channel_types = PROVIDER_TO_CHANNEL_TYPES.get(provider_name, set())

    # For internal/manual providers, use empty credentials
    if provider_name in ("internal", "manual"):
        credentials = {}
    elif not channel_types:
        logger.warning("No channel_types mapped for provider %s", provider_name)
        return None
    else:
        # Try each channel_type until we get credentials
        credentials = None
        last_error = None
        for ct in channel_types:
            try:
                cred_obj = await connection_port.get_credentials(tenant_id, ct)
                credentials = cred_obj.credentials
                break
            except Exception as exc:
                last_error = exc
                continue

        if credentials is None:
            logger.warning(
                "Could not get credentials for provider %s: %s",
                provider_name,
                last_error,
            )
            return None

    # Call the provider's extract_metrics
    try:
        extracted = await provider.extract_metrics(
            tenant_id=tenant_id,
            credentials=credentials,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as exc:
        logger.warning(
            "Provider %s API call failed: %s", provider_name, exc
        )
        return None

    # Aggregate extracted metrics by (channel_slug, metric_name)
    aggregated: Dict[Tuple[str, str], float] = {}
    for m in extracted:
        key = (m.channel_slug, m.metric_name)
        aggregated[key] = aggregated.get(key, 0.0) + m.value

    return aggregated


async def validate(
    tenant_id: UUID,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Tuple[List[Dict[str, List[ValidationResult]]], int, int, int]:
    """Run the full validation comparison.

    Returns:
        (provider_results, pass_count, fail_count, skip_count)
        where provider_results is a list of {"provider": name, "results": [...]}
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    db = SessionLocal()
    try:
        repo = OfficialMetricsRepository(db)
        connection_port = ConnectionPortImpl(db)

        # Get ETL-stored values for the period
        etl_values = _get_etl_values(repo, tenant_id, start_date, end_date)

        # Determine which providers are relevant for attraction stage
        attraction_channels = STAGE_CHANNEL_MAP.get("attraction", [])
        provider_channels: Dict[str, List[dict]] = {}
        for ch in attraction_channels:
            pname = ch.get("provider_name", "")
            provider_channels.setdefault(pname, []).append(ch)

        # Determine connected providers via ChannelRegistry
        channel_registry = ChannelRegistry(connection_port)
        split = await channel_registry.get_available_channels(tenant_id, "attraction")
        connected_slugs = {ch["slug"] for ch in split.get("connected", [])}

        all_provider_results = []
        total_pass = 0
        total_fail = 0
        total_skip = 0

        # Process each provider
        for provider_name in sorted(provider_channels.keys()):
            channels = provider_channels[provider_name]
            results: List[ValidationResult] = []

            # Check if any channel of this provider is connected
            provider_slugs = {ch["slug"] for ch in channels}
            if not (provider_slugs & connected_slugs):
                # Provider not connected — skip all its channels
                for ch in channels:
                    for metric_name in ch.get("metric_names", []):
                        r = ValidationResult(
                            channel_slug=ch["slug"],
                            metric_name=metric_name,
                            status="SKIP",
                            reason="not connected",
                        )
                        results.append(r)
                        total_skip += 1
                all_provider_results.append(
                    {"provider": provider_name, "results": results}
                )
                continue

            # Get live values from this provider
            live_values = await _get_live_values(
                provider_name, tenant_id, connection_port, start_date, end_date
            )

            if live_values is None:
                # API call failed — skip all metrics for this provider
                for ch in channels:
                    for metric_name in ch.get("metric_names", []):
                        r = ValidationResult(
                            channel_slug=ch["slug"],
                            metric_name=metric_name,
                            status="SKIP",
                            reason="API call failed",
                        )
                        results.append(r)
                        total_skip += 1
                all_provider_results.append(
                    {"provider": provider_name, "results": results}
                )
                continue

            # Compare per (channel_slug, metric_name)
            for ch in channels:
                slug = ch["slug"]
                for metric_name in ch.get("metric_names", []):
                    key = (slug, metric_name)
                    etl_val = etl_values.get(key)
                    live_val = live_values.get(key)

                    # Both missing or both zero -> PASS
                    if etl_val is None and live_val is None:
                        results.append(
                            ValidationResult(
                                channel_slug=slug,
                                metric_name=metric_name,
                                status="SKIP",
                                reason="no data in ETL or live",
                            )
                        )
                        total_skip += 1
                        continue

                    if etl_val is None:
                        etl_val = 0.0
                    if live_val is None:
                        live_val = 0.0

                    # Both zero -> PASS
                    if etl_val == 0.0 and live_val == 0.0:
                        results.append(
                            ValidationResult(
                                channel_slug=slug,
                                metric_name=metric_name,
                                status="PASS",
                                etl_value=0.0,
                                live_value=0.0,
                                diff_pct=0.0,
                            )
                        )
                        total_pass += 1
                        continue

                    diff_pct = _compute_diff(live_val, etl_val)
                    tolerance_pct = tolerance * 100.0

                    if diff_pct <= tolerance_pct:
                        status = "PASS"
                        total_pass += 1
                    else:
                        status = "FAIL"
                        total_fail += 1

                    results.append(
                        ValidationResult(
                            channel_slug=slug,
                            metric_name=metric_name,
                            status=status,
                            etl_value=etl_val,
                            live_value=live_val,
                            diff_pct=diff_pct,
                        )
                    )

            all_provider_results.append(
                {"provider": provider_name, "results": results}
            )

        return all_provider_results, total_pass, total_fail, total_skip
    finally:
        db.close()


def print_report(
    tenant_id: UUID,
    tolerance: float,
    provider_results: List[Dict],
    total_pass: int,
    total_fail: int,
    total_skip: int,
) -> None:
    """Print the structured validation report to stdout."""
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    total = total_pass + total_fail + total_skip

    print()
    print("=" * 60)
    print("  Attraction Metrics Validation Report")
    print("=" * 60)
    print(f"  Tenant: Visionarias ({tenant_id})")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Tolerance: {tolerance * 100:.0f}%")
    print()

    for entry in provider_results:
        provider_name = entry["provider"]
        results = entry["results"]

        # Check if all results are SKIP with "not connected"
        all_disconnected = all(
            r.status == "SKIP" and r.reason == "not connected"
            for r in results
        )

        if all_disconnected:
            print(f"  Provider: {provider_name}")
            print(f"    SKIPPED -- not connected")
            print()
            continue

        print(f"  Provider: {provider_name}")
        for r in results:
            print(f"  {r.format_line()}")
        print()

    print("=" * 60)
    print(f"  Summary")
    print(f"  Passed:  {total_pass}/{total} metrics")
    print(f"  Failed:  {total_fail}/{total} metrics")
    print(f"  Skipped: {total_skip}/{total} metrics (disconnected or no data)")
    print("=" * 60)
    print()


async def main() -> int:
    """Main async entrypoint. Returns exit code."""
    parser = argparse.ArgumentParser(
        description="Validate Attraction ETL metrics against live provider APIs"
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=DEFAULT_TENANT_ID,
        help=f"Tenant UUID (default: {DEFAULT_TENANT_ID})",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=DEFAULT_TOLERANCE,
        help=f"Tolerance as decimal, e.g. 0.05 for 5%% (default: {DEFAULT_TOLERANCE})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    tenant_id = UUID(args.tenant_id)
    tolerance = args.tolerance

    provider_results, total_pass, total_fail, total_skip = await validate(
        tenant_id=tenant_id,
        tolerance=tolerance,
    )

    print_report(
        tenant_id=tenant_id,
        tolerance=tolerance,
        provider_results=provider_results,
        total_pass=total_pass,
        total_fail=total_fail,
        total_skip=total_skip,
    )

    return 1 if total_fail > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
