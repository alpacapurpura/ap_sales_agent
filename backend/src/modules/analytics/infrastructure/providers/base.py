"""Base provider ABC and ExtractedMetric value object.

Every metrics provider (Meta, Google, TikTok, etc.) implements
BaseMetricsProvider so the ETL pipeline can extract from any
source through a uniform interface.
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExtractedMetric(BaseModel):
    """Raw metric extracted from a provider API.

    Carries all dimensions needed for staging and later promotion
    to official metrics.
    """

    provider: str
    channel_slug: str
    metric_name: str
    value: float
    unit: str
    currency: Optional[str] = None
    date: date
    campaign_id: Optional[str] = None
    ad_set_id: Optional[str] = None
    ad_id: Optional[str] = None
    extra: Dict = Field(default_factory=dict)


class BaseMetricsProvider(ABC):
    """Abstract base for all metrics providers.

    A new provider is added by subclassing this ABC and implementing
    the three abstract methods. No changes to service or API layers required.
    """

    @abstractmethod
    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        """Extract metrics from the provider API for the given date range."""
        ...

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        """Extract metrics with per-day granularity.

        Default implementation iterates day-by-day calling extract_metrics.
        Providers should override for optimized daily queries (e.g. date dimension).
        """
        metrics: List[ExtractedMetric] = []
        current = start_date
        while current <= end_date:
            day_metrics = await self.extract_metrics(
                tenant_id, credentials, current, current, stage=stage
            )
            metrics.extend(day_metrics)
            current += timedelta(days=1)
        return metrics

    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier for this provider (e.g. 'meta', 'google_analytics')."""
        ...

    @abstractmethod
    def rate_limit_config(self) -> dict:
        """Return rate limit configuration for this provider.

        Example: {"requests_per_minute": 60, "burst_size": 10}
        """
        ...
