"""Repository for opportunity-stage (Stage 3) metric queries.

Wraps CRM queries for SQL transition counting, checkout event aggregation,
meeting event aggregation, and payment link event counting.
Follows the same pattern as NurtureMetricsRepository.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.customer_model import (
    JourneyEventModel,
)
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)
from src.shared.domain.enums import LifecycleStage

logger = logging.getLogger(__name__)


class OpportunityMetricsRepository:
    """CRM-based SQL counting, checkout event aggregation, and meeting metrics."""

    def __init__(self, db: Session):
        self.db = db

    def count_new_sqls(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count distinct profiles that transitioned TO SQL stage within period."""
        stmt = select(
            func.count(func.distinct(LifecycleTransitionModel.profile_id)),
        ).where(
            LifecycleTransitionModel.tenant_id == tenant_id,
            LifecycleTransitionModel.to_stage == LifecycleStage.SQL,
            LifecycleTransitionModel.occurred_at >= start_date,
            LifecycleTransitionModel.occurred_at <= end_date,
        )
        result = self.db.execute(stmt).scalar()
        return int(result) if result else 0

    def count_mqls_in_period(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count distinct profiles that transitioned TO MQL stage (mini funnel source)."""
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

    def count_checkout_events(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, dict[str, Any]]:
        """Count checkout_initiated and cart_abandoned journey_events.

        Returns: {
            "checkout_initiated": {"count": int, "value": float},
            "cart_abandoned": {"count": int, "value": float},
        }
        """
        event_names = ["checkout_initiated", "cart_abandoned"]

        # Count events by name
        count_stmt = (
            select(
                JourneyEventModel.event_name,
                func.count(JourneyEventModel.id).label("count"),
            )
            .where(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name.in_(event_names),
                JourneyEventModel.occurred_at >= start_date,
                JourneyEventModel.occurred_at <= end_date,
            )
            .group_by(JourneyEventModel.event_name)
        )
        count_rows = self.db.execute(count_stmt).all()

        counts: dict[str, dict[str, Any]] = {
            name: {"count": 0, "value": 0.0} for name in event_names
        }
        for event_name, count in count_rows:
            counts[event_name]["count"] = int(count)

        # Sum total_price from properties JSONB for each event type
        for name in event_names:
            if counts[name]["count"] > 0:
                value_stmt = select(
                    func.coalesce(
                        func.sum(
                            cast(
                                func.jsonb_extract_path_text(
                                    JourneyEventModel.properties,
                                    "total_price",
                                ),
                                Float,
                            ),
                        ),
                        0.0,
                    ),
                ).where(
                    JourneyEventModel.tenant_id == tenant_id,
                    JourneyEventModel.event_name == name,
                    JourneyEventModel.occurred_at >= start_date,
                    JourneyEventModel.occurred_at <= end_date,
                )
                try:
                    value_result = self.db.execute(value_stmt).scalar()
                    counts[name]["value"] = float(value_result or 0.0)
                except Exception:
                    logger.warning("Could not sum total_price for %s events", name)
                    counts[name]["value"] = 0.0

        return counts

    def count_meeting_events(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Count meeting_booked, meeting_completed, meeting_no_show, meeting_rescheduled.

        Returns: {"booked": int, "completed": int, "no_show": int, "rescheduled": int}
        """
        event_names = [
            "meeting_booked",
            "meeting_completed",
            "meeting_no_show",
            "meeting_rescheduled",
        ]
        stmt = (
            select(
                JourneyEventModel.event_name,
                func.count(JourneyEventModel.id).label("count"),
            )
            .where(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name.in_(event_names),
                JourneyEventModel.occurred_at >= start_date,
                JourneyEventModel.occurred_at <= end_date,
            )
            .group_by(JourneyEventModel.event_name)
        )
        rows = self.db.execute(stmt).all()

        counts = {"booked": 0, "completed": 0, "no_show": 0, "rescheduled": 0}
        name_map = {
            "meeting_booked": "booked",
            "meeting_completed": "completed",
            "meeting_no_show": "no_show",
            "meeting_rescheduled": "rescheduled",
        }
        for event_name, count in rows:
            key = name_map.get(event_name)
            if key:
                counts[key] = int(count)
        return counts

    def count_payment_link_events(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Count payment_link_sent journey_events.

        Returns: {"count": int, "value": float}
        """
        count_stmt = select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "payment_link_sent",
            JourneyEventModel.occurred_at >= start_date,
            JourneyEventModel.occurred_at <= end_date,
        )
        count = int(self.db.execute(count_stmt).scalar() or 0)
        return {"count": count, "value": 0.0}
