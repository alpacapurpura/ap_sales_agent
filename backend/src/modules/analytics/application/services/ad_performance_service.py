"""Service for ad-level performance aggregation.

Queries official_metrics WHERE ad_id IS NOT NULL to build per-ad KPIs
for the Creativos tab dashboard.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import text

from src.modules.analytics.application.dto.campaign_dto import (
    AdMetricsDTO,
    AdPerformanceListDTO,
    FormatComparisonDTO,
    FormatComparisonItemDTO,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()

_PERIOD_TO_DAYS = {"7d": 7, "30d": 30, "90d": 90}

_FORMAT_EMOJIS = {
    "video": "\U0001f3ac",
    "carousel": "\U0001f5bc",
    "image": "\U0001f4f7",
    "unknown": "\u2753",
}


class AdPerformanceService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _date_range(self, period: str) -> tuple[date, date]:
        days = _PERIOD_TO_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        return start, end

    def get_top_ads(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str,
        limit: int = 10,
    ) -> AdPerformanceListDTO:
        start_date, end_date = self._date_range(period)

        rows = self._db.execute(
            text("""
                SELECT ad_id, metric_name,
                       SUM(value) AS total_value,
                       MAX(extra->>'ad_name') AS ad_name
                FROM official_metrics
                WHERE tenant_id = :tenant_id
                  AND channel_slug = :channel_slug
                  AND ad_id IS NOT NULL
                  AND metric_date BETWEEN :start_date AND :end_date
                GROUP BY ad_id, metric_name
            """),
            {
                "tenant_id": str(tenant_id),
                "channel_slug": channel_slug,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        ).fetchall()

        # Build lookup: {ad_id: {metric_name: value, "_ad_name": name}}
        metrics_by_ad: dict[str, dict[str, float | str]] = {}
        for row in rows:
            r = row._mapping
            aid = r["ad_id"]
            if aid not in metrics_by_ad:
                metrics_by_ad[aid] = {"_ad_name": r.get("ad_name") or aid}
            metrics_by_ad[aid][r["metric_name"]] = float(r["total_value"])

        # Build ad DTOs
        ads: list[AdMetricsDTO] = []
        for aid, m in metrics_by_ad.items():
            spend = m.get("spend", 0.0)
            conversions = m.get("conversions", 0.0)
            ads.append(
                AdMetricsDTO(
                    ad_id=aid,
                    ad_name=str(m.get("_ad_name", aid)),
                    spend=float(spend),
                    impressions=float(m.get("impressions", 0)),
                    clicks=float(m.get("clicks", 0)),
                    conversions=float(conversions),
                    roas=float(m["roas"]) if "roas" in m else None,
                    cpa=(
                        float(spend) / float(conversions) if conversions else None
                    ),
                    ctr=float(m["ctr"]) if "ctr" in m else None,
                    cpc=float(m["cpc"]) if "cpc" in m else None,
                )
            )

        # Sort by spend descending
        ads.sort(key=lambda a: a.spend, reverse=True)

        # Assign performance tags based on ROAS
        if ads:
            roas_values = [a.roas for a in ads if a.roas is not None]
            if roas_values:
                avg_roas = sum(roas_values) / len(roas_values)
                for ad in ads:
                    if ad.roas is not None:
                        if ad.roas >= avg_roas * 1.3:
                            ad.performance_tag = "top_performer"
                        elif ad.roas < avg_roas * 0.7:
                            ad.performance_tag = "underperformer"

        return AdPerformanceListDTO(
            ads=ads[:limit],
            period=period,
            total_ads=len(ads),
        )

    def get_format_comparison(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str,
    ) -> FormatComparisonDTO:
        """Aggregate metrics by ad format type.

        Format type is derived from ad metadata stored in the campaigns table.
        Falls back to 'unknown' if not available.
        """
        # Get ad-level metrics
        result = self.get_top_ads(tenant_id, channel_slug, period, limit=500)

        # Group by format_type
        by_format: dict[str, list[AdMetricsDTO]] = {}
        for ad in result.ads:
            fmt = ad.format_type or "unknown"
            by_format.setdefault(fmt, []).append(ad)

        formats: list[FormatComparisonItemDTO] = []
        max_roas = 0.0
        for fmt, fmt_ads in by_format.items():
            avg_ctr = (
                sum(a.ctr or 0 for a in fmt_ads) / len(fmt_ads) if fmt_ads else 0
            )
            roas_vals = [a.roas for a in fmt_ads if a.roas is not None]
            avg_roas = sum(roas_vals) / len(roas_vals) if roas_vals else None
            cpa_vals = [a.cpa for a in fmt_ads if a.cpa is not None]
            avg_cpa = sum(cpa_vals) / len(cpa_vals) if cpa_vals else None
            total_spend = sum(a.spend for a in fmt_ads)

            if avg_roas and avg_roas > max_roas:
                max_roas = avg_roas

            formats.append(
                FormatComparisonItemDTO(
                    format_type=fmt,
                    emoji=_FORMAT_EMOJIS.get(fmt, "\u2753"),
                    ad_count=len(fmt_ads),
                    avg_ctr=round(avg_ctr, 2),
                    avg_cpa=round(avg_cpa, 2) if avg_cpa else None,
                    avg_roas=round(avg_roas, 1) if avg_roas else None,
                    total_spend=round(total_spend, 2),
                )
            )

        # Normalize performance_score (0-100)
        if max_roas > 0:
            for f in formats:
                f.performance_score = round(
                    ((f.avg_roas or 0) / max_roas) * 100, 1
                )

        formats.sort(key=lambda f: f.performance_score, reverse=True)

        return FormatComparisonDTO(formats=formats, period=period)
