"""Repository for CRM-based lead count aggregation.

Wraps CRM queries for the analytics module (DDD boundary -- analytics does
not import CRM models directly in the service layer).
"""

import logging
from datetime import datetime
from uuid import UUID

from luana_core_platform.infrastructure.models.crm import (
    CustomerProfileModel,
    JourneyEventModel,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CaptureMetricsRepository:
    """CRM-based lead count and conversation aggregation for capture metrics."""

    def __init__(self, db: Session) -> None:
        """Initialize capture metrics repository."""
        self.db = db

    def count_leads_by_source(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Count net-new profiles by lead_source within date range.

        Returns: {"ig-dm": 45, "landing-form": 120, ...}
        Filters: tenant_id, first_seen_at in range, lead_source not null, not soft-deleted.
        """
        stmt = (
            select(
                CustomerProfileModel.lead_source,
                func.count(CustomerProfileModel.id).label("lead_count"),
            )
            .where(
                CustomerProfileModel.tenant_id == tenant_id,
                CustomerProfileModel.first_seen_at >= start_date,
                CustomerProfileModel.first_seen_at <= end_date,
                CustomerProfileModel.lead_source.isnot(None),
                CustomerProfileModel.is_inactive == False,
            )
            .group_by(CustomerProfileModel.lead_source)
        )
        rows = self.db.execute(stmt).all()
        result = {row.lead_source: row.lead_count for row in rows}

        # Consolidate manychat-ig leads under ig-dm (same person, unified card)
        mc_ig = result.pop("manychat-ig", 0)
        if mc_ig:
            result["ig-dm"] = result.get("ig-dm", 0) + mc_ig

        # Same for manychat-wa → whatsapp-inbound
        mc_wa = result.pop("manychat-wa", 0)
        if mc_wa:
            result["whatsapp-inbound"] = result.get("whatsapp-inbound", 0) + mc_wa

        return result

    def count_leads_by_source_detailed(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Like count_leads_by_source but WITHOUT consolidation.

        Returns raw per-source counts for sub_sources breakdown.
        """
        stmt = (
            select(
                CustomerProfileModel.lead_source,
                func.count(CustomerProfileModel.id).label("lead_count"),
            )
            .where(
                CustomerProfileModel.tenant_id == tenant_id,
                CustomerProfileModel.first_seen_at >= start_date,
                CustomerProfileModel.first_seen_at <= end_date,
                CustomerProfileModel.lead_source.isnot(None),
                CustomerProfileModel.is_inactive == False,
            )
            .group_by(CustomerProfileModel.lead_source)
        )
        rows = self.db.execute(stmt).all()
        return {row.lead_source: row.lead_count for row in rows}

    def count_conversations_by_channel(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Count distinct conversation sessions per messaging channel.

        Queries journey_events where event_name='message_received' grouped by
        properties->channel_slug. Uses distinct profile_id as a conversation
        approximation (one conversation per profile per period).

        Returns: {"ig-dm": 140, "whatsapp-inbound": 230, ...}
        """
        # JourneyEventModel does not have session_id, so use distinct profile_id
        # as approximation for unique conversations.
        # NOTE: Add session tracking to JourneyEventModel for more accurate counts.
        channel_col = func.jsonb_extract_path_text(
            JourneyEventModel.properties,
            "channel_slug",
        ).label("channel")

        stmt = (
            select(
                channel_col,
                func.count(func.distinct(JourneyEventModel.profile_id)).label(
                    "conv_count",
                ),
            )
            .where(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name == "message_received",
                JourneyEventModel.occurred_at >= start_date,
                JourneyEventModel.occurred_at <= end_date,
            )
            .group_by(channel_col)
        )
        rows = self.db.execute(stmt).all()
        return {row.channel: row.conv_count for row in rows if row.channel}
