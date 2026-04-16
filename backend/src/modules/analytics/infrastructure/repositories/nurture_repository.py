"""Repository for nurture-stage (Stage 2) metric queries.

Wraps CRM queries for MQL transition counting and email engagement
aggregation. Follows the same pattern as CaptureMetricsRepository.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.shared.domain.enums import LifecycleStage
from src.shared.infrastructure.models.crm import (
    CustomerProfileModel,
    JourneyEventModel,
    LifecycleTransitionModel,
)

logger = logging.getLogger(__name__)


class NurtureMetricsRepository:
    """CRM-based MQL counting, source attribution, and email event aggregation."""

    def __init__(self, db: Session) -> None:
        """Initialize nurture metrics repository."""
        self.db = db

    def count_new_mqls(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count distinct profiles that transitioned TO MQL stage within period.

        Uses lifecycle_transitions table where to_stage = 'mql'.
        """
        stmt = select(
            func.count(func.distinct(LifecycleTransitionModel.profile_id)),
        ).where(
            LifecycleTransitionModel.tenant_id == tenant_id,
            LifecycleTransitionModel.to_stage == LifecycleStage.MQL,
            LifecycleTransitionModel.occurred_at >= start_date,
            LifecycleTransitionModel.occurred_at <= end_date,
        )
        result = self.db.execute(stmt).scalar()
        return int(result) if result else 0

    def count_leads_in_period(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count total leads (profiles with lifecycle_stage >= LEAD) created in period.

        This is the denominator for MQL conversion rate.
        """
        stmt = select(func.count(CustomerProfileModel.id)).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.first_seen_at >= start_date,
            CustomerProfileModel.first_seen_at <= end_date,
            CustomerProfileModel.lifecycle_stage.in_(
                [
                    LifecycleStage.LEAD,
                    LifecycleStage.MQL,
                    LifecycleStage.SQL,
                    LifecycleStage.OPPORTUNITY,
                    LifecycleStage.CUSTOMER,
                    LifecycleStage.EVANGELIST,
                ],
            ),
            CustomerProfileModel.is_inactive == False,
        )
        result = self.db.execute(stmt).scalar()
        return int(result) if result else 0

    def get_mql_sources(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Group MQL transitions by lead_source to attribute to channels.

        Joins lifecycle_transitions (to_stage=MQL) with customer_profiles (lead_source).
        Returns: {'mailerlite': 5, 'ig-dm': 3, ...}
        """
        stmt = (
            select(
                CustomerProfileModel.lead_source,
                func.count(func.distinct(LifecycleTransitionModel.profile_id)).label(
                    "count",
                ),
            )
            .join(
                CustomerProfileModel,
                LifecycleTransitionModel.profile_id == CustomerProfileModel.id,
            )
            .where(
                LifecycleTransitionModel.tenant_id == tenant_id,
                LifecycleTransitionModel.to_stage == LifecycleStage.MQL,
                LifecycleTransitionModel.occurred_at >= start_date,
                LifecycleTransitionModel.occurred_at <= end_date,
                CustomerProfileModel.lead_source.isnot(None),
            )
            .group_by(CustomerProfileModel.lead_source)
        )
        rows = self.db.execute(stmt).all()
        return {row.lead_source: row.count for row in rows}

    def count_followup_events(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Count AI SDR followup events from journey_events.

        Returns: {'sent': N, 'replied': N}
        """
        sent_stmt = select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "sdr_followup_sent",
            JourneyEventModel.occurred_at >= start_date,
            JourneyEventModel.occurred_at <= end_date,
        )
        replied_stmt = select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "sdr_followup_replied",
            JourneyEventModel.occurred_at >= start_date,
            JourneyEventModel.occurred_at <= end_date,
        )
        sent = self.db.execute(sent_stmt).scalar() or 0
        replied = self.db.execute(replied_stmt).scalar() or 0
        return {"sent": int(sent), "replied": int(replied)}

    def count_email_events(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Count email engagement events from journey_events.

        Returns: {'emails_sent': N, 'opens': N, 'clicks': N}
        """
        opens_stmt = select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "email_opened",
            JourneyEventModel.occurred_at >= start_date,
            JourneyEventModel.occurred_at <= end_date,
        )
        clicks_stmt = select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "email_clicked",
            JourneyEventModel.occurred_at >= start_date,
            JourneyEventModel.occurred_at <= end_date,
        )
        sent_stmt = select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "email_sent",
            JourneyEventModel.occurred_at >= start_date,
            JourneyEventModel.occurred_at <= end_date,
        )
        opens = self.db.execute(opens_stmt).scalar() or 0
        clicks = self.db.execute(clicks_stmt).scalar() or 0
        sent = self.db.execute(sent_stmt).scalar() or 0
        return {"emails_sent": int(sent), "opens": int(opens), "clicks": int(clicks)}
