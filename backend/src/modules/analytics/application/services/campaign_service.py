"""Campaign management service — queries campaign hierarchy data."""

import logging
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
                    (SELECT COUNT(*) FROM ad_sets s
                     WHERE s.tenant_id = c.tenant_id
                       AND s.campaign_external_id = c.external_id
                       AND s.deleted_at IS NULL) AS ad_sets_count,
                    (SELECT COUNT(*) FROM ads a
                     WHERE a.tenant_id = c.tenant_id
                       AND a.campaign_external_id = c.external_id
                       AND a.deleted_at IS NULL) AS ads_count
                FROM ad_campaigns c
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

    def get_ad_sets(self, tenant_id: UUID, campaign_external_id: str) -> list[AdSetDTO]:
        rows = self._db.execute(
            text("""
                SELECT s.*,
                    (SELECT COUNT(*) FROM ads a
                     WHERE a.tenant_id = s.tenant_id
                       AND a.ad_set_external_id = s.external_id
                       AND a.deleted_at IS NULL) AS ads_count
                FROM ad_sets s
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

    async def trigger_sync(self, tenant_id: UUID) -> dict:
        """Enqueue a campaign sync job via ARQ."""
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
