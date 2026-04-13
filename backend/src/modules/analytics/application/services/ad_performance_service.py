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
from src.shared.domain.datetime_utils import utc_today

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


def _detect_format_type(creative: dict[str, str | None]) -> str:
    """Determine ad format from creative metadata columns.

    Priority: video_id present -> "video", else -> "image" (default).
    """
    if creative.get("creative_video_id"):
        return "video"
    return "image"


def _best_thumbnail_url(
    image_url: str | None,
    thumbnail_url: str | None,
) -> str | None:
    """Pick the best available image for an ad.

    Prefers creative_image_url (full resolution, image ads) over
    thumbnail_url (64x64 preview, all ads). Meta CDN thumbnail URLs
    contain a signed hash that forbids size modifications.
    """
    return image_url or thumbnail_url


class AdPerformanceService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _date_range(self, period: str) -> tuple[date, date]:
        days = _PERIOD_TO_DAYS.get(period, 30)
        end = utc_today()
        start = end - timedelta(days=days)
        return start, end

    def _detect_currency(self, tenant_id: UUID, channel_slug: str) -> str | None:
        """Read the currency stored in official_metrics for this channel."""
        row = self._db.execute(
            text("""
                SELECT currency FROM official_metrics
                WHERE tenant_id = :tenant_id
                  AND channel_slug = :channel_slug
                  AND currency IS NOT NULL
                LIMIT 1
            """),
            {"tenant_id": str(tenant_id), "channel_slug": channel_slug},
        ).fetchone()
        return row._mapping["currency"] if row else None

    def _fetch_creative_metadata(
        self,
        tenant_id: UUID,
        ad_external_ids: list[str],
    ) -> dict[str, dict[str, str | None]]:
        """Bulk-fetch creative columns from ads table for format detection.

        Returns a lookup: {external_id: {creative_video_id, creative_image_url, ...}}.
        Uses a single query for all ad_ids to avoid N+1.
        """
        if not ad_external_ids:
            return {}

        placeholders = ", ".join(f":aid_{i}" for i in range(len(ad_external_ids)))
        params: dict[str, str] = {"tenant_id": str(tenant_id)}
        params.update({f"aid_{i}": eid for i, eid in enumerate(ad_external_ids)})

        rows = self._db.execute(
            text(f"""
                SELECT a.external_id, a.creative_video_id,
                       a.creative_image_url, a.creative_thumbnail_url,
                       a.preview_shareable_link, a.creative_body,
                       a.creative_cta, a.effective_status,
                       a.campaign_external_id,
                       c.name AS campaign_name
                FROM ads a
                LEFT JOIN ad_campaigns c
                    ON c.tenant_id = a.tenant_id
                   AND c.external_id = a.campaign_external_id
                   AND c.deleted_at IS NULL
                WHERE a.tenant_id = :tenant_id
                  AND a.external_id IN ({placeholders})
                  AND a.deleted_at IS NULL
            """),  # noqa: S608 — placeholders are parameterised, not user input
            params,
        ).fetchall()

        lookup: dict[str, dict[str, str | None]] = {}
        for row in rows:
            r = row._mapping
            lookup[r["external_id"]] = {
                "creative_video_id": r.get("creative_video_id"),
                "creative_image_url": r.get("creative_image_url"),
                "creative_thumbnail_url": r.get("creative_thumbnail_url"),
                "preview_shareable_link": r.get("preview_shareable_link"),
                "creative_body": r.get("creative_body"),
                "creative_cta": r.get("creative_cta"),
                "effective_status": r.get("effective_status"),
                "campaign_name": r.get("campaign_name"),
            }

        logger.info(
            "creative_metadata_fetched",
            tenant_id=str(tenant_id),
            requested=len(ad_external_ids),
            found=len(lookup),
        )
        return lookup

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

        # Fetch creative metadata from ads table (bulk query for all ad_ids)
        creative_lookup = self._fetch_creative_metadata(
            tenant_id,
            list(metrics_by_ad.keys()),
        )

        # Build ad DTOs
        ads: list[AdMetricsDTO] = []
        for aid, m in metrics_by_ad.items():
            spend = m.get("spend", 0.0)
            conversions = m.get("conversions", 0.0)
            creative = creative_lookup.get(aid, {})
            format_type = _detect_format_type(creative)
            thumb = _best_thumbnail_url(
                creative.get("creative_image_url"),
                creative.get("creative_thumbnail_url"),
            )
            ads.append(
                AdMetricsDTO(
                    ad_id=aid,
                    ad_name=str(m.get("_ad_name", aid)),
                    campaign_name=creative.get("campaign_name"),
                    format_type=format_type,
                    thumbnail_url=thumb,
                    preview_url=creative.get("preview_shareable_link"),
                    creative_body=creative.get("creative_body"),
                    creative_cta=creative.get("creative_cta"),
                    effective_status=creative.get("effective_status"),
                    spend=float(spend),
                    impressions=float(m.get("impressions", 0)),
                    clicks=float(m.get("clicks", 0)),
                    conversions=float(conversions),
                    roas=float(m["roas"]) if "roas" in m else None,
                    cpa=(float(spend) / float(conversions) if conversions else None),
                    ctr=float(m["ctr"]) if "ctr" in m else None,
                    cpc=float(m["cpc"]) if "cpc" in m else None,
                ),
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

        currency = self._detect_currency(tenant_id, channel_slug)

        return AdPerformanceListDTO(
            ads=ads[:limit],
            period=period,
            total_ads=len(ads),
            currency=currency,
        )

    def get_format_comparison(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str,
    ) -> FormatComparisonDTO:
        """Aggregate metrics by ad format type.

        Format type is derived from creative metadata stored in the ads table.
        Falls back to 'image' when creative data is not available.
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
            avg_ctr = sum(a.ctr or 0 for a in fmt_ads) / len(fmt_ads) if fmt_ads else 0
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
                ),
            )

        # Normalize performance_score (0-100)
        if max_roas > 0:
            for f in formats:
                f.performance_score = round(((f.avg_roas or 0) / max_roas) * 100, 1)

        formats.sort(key=lambda f: f.performance_score, reverse=True)

        return FormatComparisonDTO(
            formats=formats,
            period=period,
            currency=result.currency,
        )
