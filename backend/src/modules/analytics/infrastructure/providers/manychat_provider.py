"""ManyChat metrics provider -- reads from webhook-ingested official_metrics.

Unlike other providers that pull from external APIs, ManyChatProvider
reads from the official_metrics table where webhook events have been
promoted. This allows the ETL pipeline to include ManyChat in
aggregation and cache invalidation flows.
"""
from datetime import date
from uuid import UUID

from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import BaseMetricsProvider


class ManyChatProvider(BaseMetricsProvider):
    """Provider that reads pre-ingested ManyChat metrics."""

    def __init__(self, db=None):
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
        return "manychat"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 10, "burst_size": 5}
