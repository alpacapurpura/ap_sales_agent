"""Campaign management service — queries campaign hierarchy data."""

import logging
from datetime import timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.campaign_dto import (
    AdDTO,
    AdSetDTO,
    CampaignDTO,
    CampaignOverviewDTO,
    RecommendationDTO,
)
from src.shared.domain.datetime_utils import utc_today

if TYPE_CHECKING:
    from src.modules.analytics.application.dto.campaign_dto import (
        CampaignPerformanceDTO,
        CreativesOverviewDTO,
    )

logger = logging.getLogger(__name__)


class CampaignService:
    """Read-only service for campaign hierarchy queries."""

    def __init__(self, db: Session):
        self._db = db

    def get_overview(self, tenant_id: UUID) -> CampaignOverviewDTO:
        """Get campaigns summary with counts and recommendations."""
        # Campaigns with ad_sets_count and ads_count
        rows = self._db.execute(
            text("""
                SELECT c.*,
                    COALESCE(sc.ad_sets_count, 0) AS ad_sets_count,
                    COALESCE(ac.ads_count, 0) AS ads_count
                FROM ad_campaigns c
                LEFT JOIN (
                    SELECT s.campaign_external_id, s.tenant_id,
                           COUNT(*) AS ad_sets_count
                    FROM ad_sets s
                    WHERE s.tenant_id = :tenant_id
                      AND s.deleted_at IS NULL
                    GROUP BY s.campaign_external_id, s.tenant_id
                ) sc ON sc.campaign_external_id = c.external_id
                    AND sc.tenant_id = c.tenant_id
                LEFT JOIN (
                    SELECT a.campaign_external_id, a.tenant_id,
                           COUNT(*) AS ads_count
                    FROM ads a
                    WHERE a.tenant_id = :tenant_id
                      AND a.deleted_at IS NULL
                    GROUP BY a.campaign_external_id, a.tenant_id
                ) ac ON ac.campaign_external_id = c.external_id
                    AND ac.tenant_id = c.tenant_id
                WHERE c.tenant_id = :tenant_id
                  AND c.deleted_at IS NULL
                ORDER BY c.effective_status = 'ACTIVE' DESC, c.name
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchall()

        campaigns = []
        for row in rows:
            r = row._mapping
            campaigns.append(
                CampaignDTO(
                    external_id=r["external_id"],
                    name=r["name"],
                    objective=r.get("objective"),
                    status=r.get("status"),
                    effective_status=r.get("effective_status"),
                    bid_strategy=r.get("bid_strategy"),
                    daily_budget=r.get("daily_budget"),
                    lifetime_budget=r.get("lifetime_budget"),
                    budget_remaining=r.get("budget_remaining"),
                    buying_type=r.get("buying_type"),
                    start_time=r.get("start_time"),
                    stop_time=r.get("stop_time"),
                    ad_sets_count=r.get("ad_sets_count", 0),
                    ads_count=r.get("ads_count", 0),
                )
            )

        # Recommendations
        rec_rows = self._db.execute(
            text("""
                SELECT * FROM ad_recommendations
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                ORDER BY opportunity_score DESC NULLS LAST, importance, created_at DESC
                LIMIT 50
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchall()

        recommendations = []
        for row in rec_rows:
            r = row._mapping
            recommendations.append(
                RecommendationDTO(
                    recommendation_type=r["recommendation_type"],
                    source=r["source"],
                    title=r.get("title"),
                    body=r.get("body"),
                    importance=r.get("importance"),
                    lift_estimate=r.get("lift_estimate"),
                    opportunity_score=r.get("opportunity_score"),
                    url=r.get("url"),
                    object_ids=r.get("object_ids", []),
                )
            )

        active_count = sum(1 for c in campaigns if c.effective_status == "ACTIVE")

        # Last synced = most recent updated_at from ad_campaigns
        last_synced_row = self._db.execute(
            text("""
                SELECT MAX(updated_at) AS last_synced FROM ad_campaigns
                WHERE tenant_id = :tenant_id AND deleted_at IS NULL
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchone()
        last_synced = (
            last_synced_row._mapping["last_synced"] if last_synced_row else None
        )

        return CampaignOverviewDTO(
            campaigns=campaigns,
            recommendations=recommendations,
            total_campaigns=len(campaigns),
            active_campaigns=active_count,
            last_synced=last_synced,
        )

    def get_performance(
        self, tenant_id: UUID, period: str = "30d"
    ) -> "CampaignPerformanceDTO":
        """Get campaigns with aggregated metrics for the given period."""
        from src.modules.analytics.application.dto.campaign_dto import (
            CampaignMetricsDTO,
            CampaignPerformanceDTO,
            CampaignWithMetricsDTO,
        )

        # Parse period
        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        end_date = utc_today()
        start_date = end_date - timedelta(days=days)

        # 1. Campaigns with counts
        camp_rows = self._db.execute(
            text("""
                SELECT c.*,
                    COALESCE(sc.ad_sets_count, 0) AS ad_sets_count,
                    COALESCE(ac.ads_count, 0) AS ads_count
                FROM ad_campaigns c
                LEFT JOIN (
                    SELECT s.campaign_external_id, s.tenant_id,
                           COUNT(*) AS ad_sets_count
                    FROM ad_sets s
                    WHERE s.tenant_id = :tenant_id
                      AND s.deleted_at IS NULL
                    GROUP BY s.campaign_external_id, s.tenant_id
                ) sc ON sc.campaign_external_id = c.external_id
                    AND sc.tenant_id = c.tenant_id
                LEFT JOIN (
                    SELECT a.campaign_external_id, a.tenant_id,
                           COUNT(*) AS ads_count
                    FROM ads a
                    WHERE a.tenant_id = :tenant_id
                      AND a.deleted_at IS NULL
                    GROUP BY a.campaign_external_id, a.tenant_id
                ) ac ON ac.campaign_external_id = c.external_id
                    AND ac.tenant_id = c.tenant_id
                WHERE c.tenant_id = :tenant_id
                  AND c.deleted_at IS NULL
                ORDER BY
                    CASE c.effective_status
                        WHEN 'ACTIVE' THEN 1
                        WHEN 'WITH_ISSUES' THEN 2
                        WHEN 'IN_PROCESS' THEN 3
                        WHEN 'PAUSED' THEN 4
                        ELSE 5
                    END,
                    c.name
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchall()

        # 2. Metrics aggregated by campaign_id for the period
        metric_rows = self._db.execute(
            text("""
                SELECT campaign_id, metric_name,
                       SUM(value) AS total_value
                FROM official_metrics
                WHERE tenant_id = :tenant_id
                  AND channel_slug = 'meta-ads'
                  AND campaign_id IS NOT NULL
                  AND metric_date BETWEEN :start_date AND :end_date
                GROUP BY campaign_id, metric_name
            """),
            {
                "tenant_id": str(tenant_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        ).fetchall()

        # Build metrics lookup: {campaign_id: {metric_name: value}}
        metrics_by_campaign: dict[str, dict[str, float]] = {}
        for row in metric_rows:
            r = row._mapping
            cid = r["campaign_id"]
            if cid not in metrics_by_campaign:
                metrics_by_campaign[cid] = {}
            metrics_by_campaign[cid][r["metric_name"]] = float(r["total_value"])

        # 3. Build campaign list with metrics
        campaigns: list[CampaignWithMetricsDTO] = []
        all_cpas: list[float] = []

        for row in camp_rows:
            r = row._mapping
            ext_id = r["external_id"]
            m = metrics_by_campaign.get(ext_id, {})

            spend = m.get("spend", 0.0)
            conversions = m.get("conversions", 0.0)
            clicks = m.get("clicks", 0.0)
            impressions = m.get("impressions", 0.0)

            cpa = spend / conversions if conversions > 0 else None
            roas_val = m.get("ROAS")
            ctr = (clicks / impressions * 100) if impressions > 0 else None
            cpc = spend / clicks if clicks > 0 else None
            cpm = (spend / impressions * 1000) if impressions > 0 else None

            metrics_dto = CampaignMetricsDTO(
                spend=spend,
                conversions=conversions,
                cpa=round(cpa, 2) if cpa is not None else None,
                roas=round(float(roas_val), 2) if roas_val else None,
                ctr=round(ctr, 2) if ctr is not None else None,
                cpc=round(cpc, 2) if cpc is not None else None,
                cpm=round(cpm, 2) if cpm is not None else None,
                frequency=m.get("frequency"),
                impressions=impressions,
                clicks=clicks,
                reach=m.get("reach", 0.0),
            )

            if cpa is not None:
                all_cpas.append(cpa)

            campaigns.append(
                CampaignWithMetricsDTO(
                    external_id=ext_id,
                    name=r["name"],
                    objective=r.get("objective"),
                    status=r.get("status"),
                    effective_status=r.get("effective_status"),
                    daily_budget=r.get("daily_budget"),
                    lifetime_budget=r.get("lifetime_budget"),
                    budget_remaining=r.get("budget_remaining"),
                    start_time=r.get("start_time"),
                    stop_time=r.get("stop_time"),
                    ad_sets_count=r.get("ad_sets_count", 0),
                    ads_count=r.get("ads_count", 0),
                    metrics=metrics_dto,
                    health="good",  # placeholder, computed below
                )
            )

        # 4. Compute health based on CPA vs average
        avg_cpa = sum(all_cpas) / len(all_cpas) if all_cpas else None
        for camp in campaigns:
            if camp.metrics.cpa is not None and avg_cpa and avg_cpa > 0:
                ratio = camp.metrics.cpa / avg_cpa
                if ratio > 3:
                    camp.health = "critical"
                elif ratio > 1.8:
                    camp.health = "warning"
                else:
                    camp.health = "good"
            elif camp.effective_status == "WITH_ISSUES":
                camp.health = "critical"

        # 5. Recommendations
        rec_rows = self._db.execute(
            text("""
                SELECT * FROM ad_recommendations
                WHERE tenant_id = :tenant_id
                  AND deleted_at IS NULL
                ORDER BY opportunity_score DESC NULLS LAST, importance, created_at DESC
                LIMIT 20
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchall()

        recommendations = [
            RecommendationDTO(
                recommendation_type=r._mapping["recommendation_type"],
                source=r._mapping["source"],
                title=r._mapping.get("title"),
                body=r._mapping.get("body"),
                importance=r._mapping.get("importance"),
                lift_estimate=r._mapping.get("lift_estimate"),
                opportunity_score=r._mapping.get("opportunity_score"),
                url=r._mapping.get("url"),
                object_ids=r._mapping.get("object_ids", []),
            )
            for r in rec_rows
        ]

        # 6. Currency from official_metrics
        currency_row = self._db.execute(
            text("""
                SELECT currency FROM official_metrics
                WHERE tenant_id = :tenant_id
                  AND channel_slug = 'meta-ads'
                  AND currency IS NOT NULL
                LIMIT 1
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchone()
        currency = currency_row._mapping["currency"] if currency_row else None

        # 7. Last synced
        last_synced_row = self._db.execute(
            text("""
                SELECT MAX(updated_at) AS last_synced FROM ad_campaigns
                WHERE tenant_id = :tenant_id AND deleted_at IS NULL
            """),
            {"tenant_id": str(tenant_id)},
        ).fetchone()
        last_synced = (
            last_synced_row._mapping["last_synced"] if last_synced_row else None
        )

        active_count = sum(1 for c in campaigns if c.effective_status == "ACTIVE")

        return CampaignPerformanceDTO(
            campaigns=campaigns,
            recommendations=recommendations,
            total_campaigns=len(campaigns),
            active_campaigns=active_count,
            currency=currency,
            last_synced=last_synced,
        )

    def get_ad_sets(self, tenant_id: UUID, campaign_external_id: str) -> list[AdSetDTO]:
        rows = self._db.execute(
            text("""
                SELECT s.*,
                    COALESCE(ac.ads_count, 0) AS ads_count
                FROM ad_sets s
                LEFT JOIN (
                    SELECT a.ad_set_external_id, a.tenant_id,
                           COUNT(*) AS ads_count
                    FROM ads a
                    WHERE a.tenant_id = :tenant_id
                      AND a.deleted_at IS NULL
                    GROUP BY a.ad_set_external_id, a.tenant_id
                ) ac ON ac.ad_set_external_id = s.external_id
                    AND ac.tenant_id = s.tenant_id
                WHERE s.tenant_id = :tenant_id
                  AND s.campaign_external_id = :campaign_external_id
                  AND s.deleted_at IS NULL
                ORDER BY s.effective_status = 'ACTIVE' DESC, s.name
            """),
            {"tenant_id": str(tenant_id), "campaign_external_id": campaign_external_id},
        ).fetchall()

        return [
            AdSetDTO(
                external_id=r._mapping["external_id"],
                campaign_external_id=r._mapping["campaign_external_id"],
                name=r._mapping["name"],
                status=r._mapping.get("status"),
                effective_status=r._mapping.get("effective_status"),
                optimization_goal=r._mapping.get("optimization_goal"),
                targeting_summary=r._mapping.get("targeting"),
                learning_stage=r._mapping.get("learning_stage"),
                daily_budget=r._mapping.get("daily_budget"),
                ads_count=r._mapping.get("ads_count", 0),
            )
            for r in rows
        ]

    def get_ads(self, tenant_id: UUID, ad_set_external_id: str) -> list[AdDTO]:
        rows = self._db.execute(
            text("""
                SELECT * FROM ads
                WHERE tenant_id = :tenant_id
                  AND ad_set_external_id = :ad_set_external_id
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "ad_set_external_id": ad_set_external_id},
        ).fetchall()

        return [
            AdDTO(
                external_id=r._mapping["external_id"],
                name=r._mapping["name"],
                status=r._mapping.get("status"),
                effective_status=r._mapping.get("effective_status"),
                creative_thumbnail_url=r._mapping.get("creative_thumbnail_url"),
                creative_title=r._mapping.get("creative_title"),
                creative_cta=r._mapping.get("creative_cta"),
                preview_shareable_link=r._mapping.get("preview_shareable_link"),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Creatives / Ad Gallery
    # ------------------------------------------------------------------

    _CREATIVES_ADS_SQL = text("""
        SELECT a.external_id,
               a.name,
               c.name AS campaign_name,
               a.campaign_external_id,
               a.status,
               a.effective_status,
               a.creative_thumbnail_url,
               a.creative_title,
               a.creative_cta,
               a.preview_shareable_link
        FROM ads a
        LEFT JOIN ad_campaigns c
            ON c.tenant_id = a.tenant_id
           AND c.external_id = a.campaign_external_id
           AND c.deleted_at IS NULL
        WHERE a.tenant_id = :tenant_id
          AND a.deleted_at IS NULL
        ORDER BY
            CASE a.effective_status
                WHEN 'ACTIVE' THEN 1
                WHEN 'WITH_ISSUES' THEN 2
                WHEN 'IN_PROCESS' THEN 3
                WHEN 'PAUSED' THEN 4
                ELSE 5
            END,
            a.name
    """)

    _VIDEO_RETENTION_SQL = text("""
        SELECT metric_name,
               SUM(value) AS total_value
        FROM official_metrics
        WHERE tenant_id = :tenant_id
          AND channel_slug = 'meta-ads'
          AND metric_name IN (
              'meta_video_views',
              'meta_video_p25',
              'meta_video_p50',
              'meta_video_p75',
              'meta_video_p100',
              'meta_video_30sec',
              'meta_video_avg_watch_time'
          )
          AND metric_date BETWEEN :start_date AND :end_date
        GROUP BY metric_name
    """)

    def get_creatives_overview(
        self, tenant_id: UUID, period: str = "30d"
    ) -> "CreativesOverviewDTO":
        """Get ad gallery with creative details and video retention metrics."""
        from src.modules.analytics.application.dto.campaign_dto import (
            AdPerformanceDTO,
            CreativesOverviewDTO,
            VideoRetentionDTO,
        )

        days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
        end_date = utc_today()
        start_date = end_date - timedelta(days=days)

        # 1. Ads with campaign names
        ad_rows = self._db.execute(
            self._CREATIVES_ADS_SQL,
            {"tenant_id": str(tenant_id)},
        ).fetchall()

        ads = [
            AdPerformanceDTO(
                external_id=r._mapping["external_id"],
                name=r._mapping["name"],
                campaign_name=r._mapping.get("campaign_name"),
                campaign_external_id=r._mapping.get("campaign_external_id"),
                status=r._mapping.get("status"),
                effective_status=r._mapping.get("effective_status"),
                creative_thumbnail_url=r._mapping.get("creative_thumbnail_url"),
                creative_title=r._mapping.get("creative_title"),
                creative_cta=r._mapping.get("creative_cta"),
                preview_shareable_link=r._mapping.get("preview_shareable_link"),
            )
            for r in ad_rows
        ]

        # 2. Video retention metrics
        vr_rows = self._db.execute(
            self._VIDEO_RETENTION_SQL,
            {
                "tenant_id": str(tenant_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        ).fetchall()

        vr_map: dict[str, float] = {}
        for row in vr_rows:
            r = row._mapping
            vr_map[r["metric_name"]] = float(r["total_value"])

        video_retention = VideoRetentionDTO(
            plays=vr_map.get("meta_video_views", 0),
            p25=vr_map.get("meta_video_p25", 0),
            p50=vr_map.get("meta_video_p50", 0),
            p75=vr_map.get("meta_video_p75", 0),
            p100=vr_map.get("meta_video_p100", 0),
            views_30s=vr_map.get("meta_video_30sec", 0),
            avg_watch_time=vr_map.get("meta_video_avg_watch_time", 0),
        )

        return CreativesOverviewDTO(
            ads=ads,
            video_retention=video_retention,
            total_ads=len(ads),
        )

    async def trigger_sync(self, tenant_id: UUID) -> dict:
        """Run campaign sync inline (synchronous) with ARQ fallback.

        Prefers inline execution so results are available immediately.
        Falls back to ARQ enqueue if inline fails.
        """
        try:
            return await self._sync_campaigns_inline(tenant_id)
        except Exception as exc:
            logger.warning("Inline campaign sync failed, falling back to ARQ: %s", exc)
            return await self._enqueue_campaign_sync_arq(tenant_id)

    async def _sync_campaigns_inline(self, tenant_id: UUID) -> dict:
        """Execute campaign sync synchronously (inline, no worker needed)."""
        from src.modules.analytics.infrastructure.providers.meta_campaign_provider import (
            MetaCampaignProvider,
        )
        from src.modules.analytics.infrastructure.repositories.campaign_repository import (
            CampaignRepository,
        )
        from src.modules.analytics.infrastructure.sync.campaign_sync_pipeline import (
            CampaignSyncPipeline,
        )
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        connection_port = ConnectionPortImpl(self._db)
        creds = await connection_port.get_credentials(tenant_id, "meta")
        credentials = {**creds.credentials, **creds.config}

        campaign_repo = CampaignRepository(self._db)
        campaign_provider = MetaCampaignProvider()
        pipeline = CampaignSyncPipeline(
            provider=campaign_provider,
            repository=campaign_repo,
        )

        result = await pipeline.run_sync(tenant_id, credentials)
        self._db.commit()

        return {"status": "success", **result}

    async def _enqueue_campaign_sync_arq(self, tenant_id: UUID) -> dict:
        """Fallback: enqueue a campaign sync job via ARQ."""
        from arq.connections import ArqRedis, RedisSettings, create_pool

        from src.core.config import settings as app_settings

        redis_settings = RedisSettings.from_dsn(app_settings.REDIS_URL)
        redis: ArqRedis = await create_pool(redis_settings)
        job = await redis.enqueue_job(
            "run_campaign_sync",
            str(tenant_id),
            "meta",
        )
        await redis.aclose()
        return {"status": "queued", "job_id": job.job_id if job else None}
