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
        for r in sorted(
            self.results,
            key=lambda x: (x.channel_slug, x.metric_name, x.metric_date),
        ):
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
                "date_range": [
                    self.date_range[0].isoformat(),
                    self.date_range[1].isoformat(),
                ],
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
