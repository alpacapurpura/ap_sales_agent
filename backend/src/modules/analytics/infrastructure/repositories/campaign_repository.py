"""Repository for campaign management entities.

Handles upsert operations for campaigns, ad sets, ads, and recommendations.
Uses raw SQL for COALESCE-based ON CONFLICT (matching existing metric pattern).
"""

import json
import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CampaignRepository:
    """CRUD operations for campaign hierarchy + recommendations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Campaigns ──

    _UPSERT_CAMPAIGN_SQL = text("""
        INSERT INTO ad_campaigns (
            tenant_id, provider, external_id, name, objective,
            status, effective_status, bid_strategy,
            daily_budget, lifetime_budget, budget_remaining,
            buying_type, special_ad_categories,
            start_time, stop_time,
            external_created_time, external_updated_time,
            extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :external_id, :name, :objective,
            :status, :effective_status, :bid_strategy,
            :daily_budget, :lifetime_budget, :budget_remaining,
            :buying_type, CAST(:special_ad_categories AS jsonb),
            :start_time, :stop_time,
            :external_created_time, :external_updated_time,
            CAST(:extra AS jsonb), NOW(), NOW()
        )
        ON CONFLICT (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
        DO UPDATE SET
            name = EXCLUDED.name,
            objective = EXCLUDED.objective,
            status = EXCLUDED.status,
            effective_status = EXCLUDED.effective_status,
            bid_strategy = EXCLUDED.bid_strategy,
            daily_budget = EXCLUDED.daily_budget,
            lifetime_budget = EXCLUDED.lifetime_budget,
            budget_remaining = EXCLUDED.budget_remaining,
            buying_type = EXCLUDED.buying_type,
            special_ad_categories = EXCLUDED.special_ad_categories,
            start_time = EXCLUDED.start_time,
            stop_time = EXCLUDED.stop_time,
            external_created_time = EXCLUDED.external_created_time,
            external_updated_time = EXCLUDED.external_updated_time,
            extra = EXCLUDED.extra,
            updated_at = NOW()
    """)

    def upsert_campaigns(
        self,
        tenant_id: UUID,
        campaigns: list[dict],
    ) -> int:
        count = 0
        for c in campaigns:
            self._session.execute(
                self._UPSERT_CAMPAIGN_SQL,
                {
                    "tenant_id": str(tenant_id),
                    "provider": c.get("provider", "meta"),
                    "external_id": c["external_id"],
                    "name": c.get("name", ""),
                    "objective": c.get("objective"),
                    "status": c.get("status"),
                    "effective_status": c.get("effective_status"),
                    "bid_strategy": c.get("bid_strategy"),
                    "daily_budget": c.get("daily_budget"),
                    "lifetime_budget": c.get("lifetime_budget"),
                    "budget_remaining": c.get("budget_remaining"),
                    "buying_type": c.get("buying_type", "AUCTION"),
                    "special_ad_categories": json.dumps(
                        c.get("special_ad_categories", []),
                    ),
                    "start_time": c.get("start_time"),
                    "stop_time": c.get("stop_time"),
                    "external_created_time": c.get("external_created_time"),
                    "external_updated_time": c.get("external_updated_time"),
                    "extra": json.dumps(c.get("extra", {})),
                },
            )
            count += 1
        return count

    # ── Ad Sets ──

    _UPSERT_ADSET_SQL = text("""
        INSERT INTO ad_sets (
            tenant_id, provider, external_id, campaign_external_id,
            name, status, effective_status,
            optimization_goal, billing_event, bid_strategy,
            daily_budget, lifetime_budget, budget_remaining,
            targeting, destination_type, learning_stage,
            start_time, end_time, extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :external_id, :campaign_external_id,
            :name, :status, :effective_status,
            :optimization_goal, :billing_event, :bid_strategy,
            :daily_budget, :lifetime_budget, :budget_remaining,
            CAST(:targeting AS jsonb), :destination_type, :learning_stage,
            :start_time, :end_time, CAST(:extra AS jsonb), NOW(), NOW()
        )
        ON CONFLICT (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
        DO UPDATE SET
            campaign_external_id = EXCLUDED.campaign_external_id,
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            effective_status = EXCLUDED.effective_status,
            optimization_goal = EXCLUDED.optimization_goal,
            billing_event = EXCLUDED.billing_event,
            bid_strategy = EXCLUDED.bid_strategy,
            daily_budget = EXCLUDED.daily_budget,
            lifetime_budget = EXCLUDED.lifetime_budget,
            budget_remaining = EXCLUDED.budget_remaining,
            targeting = EXCLUDED.targeting,
            destination_type = EXCLUDED.destination_type,
            learning_stage = EXCLUDED.learning_stage,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            extra = EXCLUDED.extra,
            updated_at = NOW()
    """)

    def upsert_ad_sets(
        self,
        tenant_id: UUID,
        ad_sets: list[dict],
    ) -> int:
        count = 0
        for a in ad_sets:
            self._session.execute(
                self._UPSERT_ADSET_SQL,
                {
                    "tenant_id": str(tenant_id),
                    "provider": a.get("provider", "meta"),
                    "external_id": a["external_id"],
                    "campaign_external_id": a["campaign_external_id"],
                    "name": a.get("name", ""),
                    "status": a.get("status"),
                    "effective_status": a.get("effective_status"),
                    "optimization_goal": a.get("optimization_goal"),
                    "billing_event": a.get("billing_event"),
                    "bid_strategy": a.get("bid_strategy"),
                    "daily_budget": a.get("daily_budget"),
                    "lifetime_budget": a.get("lifetime_budget"),
                    "budget_remaining": a.get("budget_remaining"),
                    "targeting": json.dumps(a.get("targeting", {})),
                    "destination_type": a.get("destination_type"),
                    "learning_stage": a.get("learning_stage"),
                    "start_time": a.get("start_time"),
                    "end_time": a.get("end_time"),
                    "extra": json.dumps(a.get("extra", {})),
                },
            )
            count += 1
        return count

    # ── Ads ──

    _UPSERT_AD_SQL = text("""
        INSERT INTO ads (
            tenant_id, provider, external_id,
            campaign_external_id, ad_set_external_id,
            name, status, effective_status,
            creative_id, creative_thumbnail_url, creative_image_url,
            creative_video_id, creative_title, creative_body,
            creative_cta, creative_link_url,
            preview_shareable_link, extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :external_id,
            :campaign_external_id, :ad_set_external_id,
            :name, :status, :effective_status,
            :creative_id, :creative_thumbnail_url, :creative_image_url,
            :creative_video_id, :creative_title, :creative_body,
            :creative_cta, :creative_link_url,
            :preview_shareable_link, CAST(:extra AS jsonb), NOW(), NOW()
        )
        ON CONFLICT (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
        DO UPDATE SET
            campaign_external_id = EXCLUDED.campaign_external_id,
            ad_set_external_id = EXCLUDED.ad_set_external_id,
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            effective_status = EXCLUDED.effective_status,
            creative_id = EXCLUDED.creative_id,
            creative_thumbnail_url = EXCLUDED.creative_thumbnail_url,
            creative_image_url = EXCLUDED.creative_image_url,
            creative_video_id = EXCLUDED.creative_video_id,
            creative_title = EXCLUDED.creative_title,
            creative_body = EXCLUDED.creative_body,
            creative_cta = EXCLUDED.creative_cta,
            creative_link_url = EXCLUDED.creative_link_url,
            preview_shareable_link = EXCLUDED.preview_shareable_link,
            extra = EXCLUDED.extra,
            updated_at = NOW()
    """)

    def upsert_ads(
        self,
        tenant_id: UUID,
        ads: list[dict],
    ) -> int:
        count = 0
        for ad in ads:
            self._session.execute(
                self._UPSERT_AD_SQL,
                {
                    "tenant_id": str(tenant_id),
                    "provider": ad.get("provider", "meta"),
                    "external_id": ad["external_id"],
                    "campaign_external_id": ad["campaign_external_id"],
                    "ad_set_external_id": ad["ad_set_external_id"],
                    "name": ad.get("name", ""),
                    "status": ad.get("status"),
                    "effective_status": ad.get("effective_status"),
                    "creative_id": ad.get("creative_id"),
                    "creative_thumbnail_url": ad.get("creative_thumbnail_url"),
                    "creative_image_url": ad.get("creative_image_url"),
                    "creative_video_id": ad.get("creative_video_id"),
                    "creative_title": ad.get("creative_title"),
                    "creative_body": ad.get("creative_body"),
                    "creative_cta": ad.get("creative_cta"),
                    "creative_link_url": ad.get("creative_link_url"),
                    "preview_shareable_link": ad.get("preview_shareable_link"),
                    "extra": json.dumps(ad.get("extra", {})),
                },
            )
            count += 1
        return count

    # ── Recommendations ──

    _UPSERT_RECOMMENDATION_SQL = text("""
        INSERT INTO ad_recommendations (
            tenant_id, provider, source, recommendation_type,
            object_ids, title, body, blame_field,
            importance, confidence, lift_estimate,
            opportunity_score, url, recommendation_signature,
            extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :source, :recommendation_type,
            CAST(:object_ids AS jsonb), :title, :body, :blame_field,
            :importance, :confidence, :lift_estimate,
            :opportunity_score, :url, :recommendation_signature,
            CAST(:extra AS jsonb), NOW(), NOW()
        )
        ON CONFLICT DO NOTHING
    """)

    def upsert_recommendations(
        self,
        tenant_id: UUID,
        recommendations: list[dict],
    ) -> int:
        count = 0
        for r in recommendations:
            self._session.execute(
                self._UPSERT_RECOMMENDATION_SQL,
                {
                    "tenant_id": str(tenant_id),
                    "provider": r.get("provider", "meta"),
                    "source": r.get("source", "account"),
                    "recommendation_type": r["recommendation_type"],
                    "object_ids": json.dumps(r.get("object_ids", [])),
                    "title": r.get("title"),
                    "body": r.get("body"),
                    "blame_field": r.get("blame_field"),
                    "importance": r.get("importance"),
                    "confidence": r.get("confidence"),
                    "lift_estimate": r.get("lift_estimate"),
                    "opportunity_score": r.get("opportunity_score"),
                    "url": r.get("url"),
                    "recommendation_signature": r.get("recommendation_signature"),
                    "extra": json.dumps(r.get("extra", {})),
                },
            )
            count += 1
        return count

    # ── Queries ──

    def get_campaigns(
        self,
        tenant_id: UUID,
        provider: str = "meta",
    ) -> list:
        result = self._session.execute(
            text("""
                SELECT * FROM ad_campaigns
                WHERE tenant_id = :tenant_id
                  AND provider = :provider
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "provider": provider},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    def get_ad_sets(
        self,
        tenant_id: UUID,
        campaign_external_id: str,
    ) -> list:
        result = self._session.execute(
            text("""
                SELECT * FROM ad_sets
                WHERE tenant_id = :tenant_id
                  AND campaign_external_id = :campaign_external_id
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "campaign_external_id": campaign_external_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    def get_ads(
        self,
        tenant_id: UUID,
        ad_set_external_id: str,
    ) -> list:
        result = self._session.execute(
            text("""
                SELECT * FROM ads
                WHERE tenant_id = :tenant_id
                  AND ad_set_external_id = :ad_set_external_id
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "ad_set_external_id": ad_set_external_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    def get_recommendations(
        self,
        tenant_id: UUID,
        provider: str = "meta",
    ) -> list:
        result = self._session.execute(
            text("""
                SELECT * FROM ad_recommendations
                WHERE tenant_id = :tenant_id
                  AND provider = :provider
                  AND deleted_at IS NULL
                ORDER BY opportunity_score DESC NULLS LAST, importance, created_at DESC
                LIMIT 50
            """),
            {"tenant_id": str(tenant_id), "provider": provider},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    def soft_delete_stale(
        self,
        tenant_id: UUID,
        provider: str,
        table: str,
        active_external_ids: list,
    ) -> int:
        """Soft-delete entities no longer returned by the API."""
        if not active_external_ids:
            return 0
        placeholders = ", ".join(f":id_{i}" for i in range(len(active_external_ids)))
        params: dict = {"tenant_id": str(tenant_id), "provider": provider}
        params.update({f"id_{i}": eid for i, eid in enumerate(active_external_ids)})
        result = self._session.execute(
            text(
                f"""
                UPDATE {table}
                SET deleted_at = NOW(), updated_at = NOW()
                WHERE tenant_id = :tenant_id
                  AND provider = :provider
                  AND deleted_at IS NULL
                  AND external_id NOT IN ({placeholders})
            """,
            ),
            params,
        )
        return result.rowcount
