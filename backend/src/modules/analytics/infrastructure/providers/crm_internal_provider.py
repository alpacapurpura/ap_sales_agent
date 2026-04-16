"""CRMInternalProvider — extracts cold contact metrics from CRM journey_events.

Channel slug: cold-contact
Metrics: contacts (outbound attempts) + responses (replies received)

Queries JourneyEventModel using SQLAlchemy 2.0 syntax, filtering by
tenant_id and outbound event types. Does not use external credentials
-- needs db_session passed via credentials["db_session"].
"""

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import func, select

from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.shared.infrastructure.models.crm import (
    JourneyEventModel,
)

logger = logging.getLogger(__name__)

# Event names that represent outbound contact attempts
OUTBOUND_CONTACT_EVENTS = {
    "outbound_contact",
    "outbound_call",
    "outbound_email",
}

# Event names that represent responses to outbound activity
OUTBOUND_RESPONSE_EVENTS = {
    "outbound_response",
    "outbound_reply",
}


class CRMInternalProvider(BaseMetricsProvider):
    """Extracts cold-contact metrics from CRM journey events."""

    def provider_name(self) -> str:
        """Execute provider name operation."""
        return "crm_internal"

    def rate_limit_config(self) -> dict:
        """Execute rate limit config operation."""
        return {"requests_per_minute": 100, "burst_size": 50}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract metrics."""
        db = credentials.get("db_session")
        if db is None:
            logger.warning("crm_internal_provider_no_db_session tenant=%s", tenant_id)
            return ExtractionResult()

        # Count outbound contacts
        contacts_stmt = (
            select(func.count())
            .select_from(JourneyEventModel)
            .where(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name.in_(OUTBOUND_CONTACT_EVENTS),
                JourneyEventModel.occurred_at >= start_date,
                JourneyEventModel.occurred_at <= end_date,
            )
        )
        contacts_result = db.execute(contacts_stmt)
        contacts_count = contacts_result.scalar() or 0

        # Count outbound responses
        responses_stmt = (
            select(func.count())
            .select_from(JourneyEventModel)
            .where(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name.in_(OUTBOUND_RESPONSE_EVENTS),
                JourneyEventModel.occurred_at >= start_date,
                JourneyEventModel.occurred_at <= end_date,
            )
        )
        responses_result = db.execute(responses_stmt)
        responses_count = responses_result.scalar() or 0

        return ExtractionResult(
            metrics=[
                ExtractedMetric(
                    provider="crm_internal",
                    channel_slug="cold-contact",
                    metric_name="contacts",
                    value=float(contacts_count),
                    unit="count",
                    date=end_date,
                ),
                ExtractedMetric(
                    provider="crm_internal",
                    channel_slug="cold-contact",
                    metric_name="responses",
                    value=float(responses_count),
                    unit="count",
                    date=end_date,
                ),
            ],
        )
