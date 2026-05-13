"""ManyChat metrics provider -- reads from webhook-ingested official_metrics.

Unlike other providers that pull from external APIs, ManyChatProvider
reads from the official_metrics table where webhook events have been
promoted. This allows the ETL pipeline to include ManyChat in
aggregation and cache invalidation flows.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_analytics_engine.domain.extraction_result import ExtractionResult
from luana_core_analytics_engine.infrastructure.providers.base import BaseMetricsProvider

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.orm import Session


class ManyChatProvider(BaseMetricsProvider):
    """Provider that reads pre-ingested ManyChat metrics."""

    def __init__(self, db: Session | None = None) -> None:
        """Initialize many chat provider."""
        self._db = db

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "capture",
    ) -> ExtractionResult:
        """Read ManyChat metrics from official_metrics (webhook-fed).

        This is a pass-through: metrics are already in the DB from
        the webhook ingestion pipeline. This method exists so the
        ETL scheduler can include ManyChat in aggregation runs.
        """
        return ExtractionResult()

    def provider_name(self) -> str:
        """Execute provider name operation."""
        return "manychat"

    def rate_limit_config(self) -> dict:
        """Execute rate limit config operation."""
        return {"requests_per_minute": 10, "burst_size": 5}
