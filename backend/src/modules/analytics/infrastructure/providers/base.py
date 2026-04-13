"""Base provider ABC and ExtractedMetric value object.

Every metrics provider (Meta, Google, TikTok, etc.) implements
BaseMetricsProvider so the ETL pipeline can extract from any
source through a uniform interface.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date, timedelta
from uuid import UUID

import sentry_sdk
import structlog
from pydantic import BaseModel, Field

from src.modules.analytics.domain.extraction_result import (
    ExtractionResult,
    SubExtractorFailure,
)

logger = structlog.get_logger(__name__)


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
    currency: str | None = None
    date: date
    campaign_id: str | None = None
    ad_set_id: str | None = None
    ad_id: str | None = None
    extra: dict = Field(default_factory=dict)


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
    ) -> ExtractionResult:
        """Extract metrics from the provider API for the given date range."""
        ...

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract metrics with per-day granularity.

        Default implementation iterates day-by-day calling extract_metrics.
        Providers should override for optimized daily queries (e.g. date dimension).
        """
        all_metrics: list[ExtractedMetric] = []
        all_failures: list[SubExtractorFailure] = []
        current = start_date
        while current <= end_date:
            day_result = await self.extract_metrics(
                tenant_id,
                credentials,
                current,
                current,
                stage=stage,
            )
            all_metrics.extend(day_result.metrics)
            all_failures.extend(day_result.failures)
            current += timedelta(days=1)
        return ExtractionResult(metrics=all_metrics, failures=all_failures)

    async def _safe_extract(
        self,
        fn: Callable,
        *args: object,
        extractor_name: str,
    ) -> tuple[list[ExtractedMetric], SubExtractorFailure | None]:
        """Run a sub-extractor safely, capturing exceptions as SubExtractorFailure.

        Tags the Sentry event with provider + sub_extractor info so alerts
        can filter by failure_type=partial.
        """
        try:
            logger.debug(
                "sub_extractor_start",
                provider=self.provider_name(),
                extractor=extractor_name,
            )
            result = await fn(*args)
            logger.info(
                "sub_extractor_complete",
                provider=self.provider_name(),
                extractor=extractor_name,
                metrics_count=len(result),
            )
        except Exception as exc:
            sentry_sdk.set_tag("provider", self.provider_name())
            sentry_sdk.set_tag("sub_extractor", extractor_name)
            sentry_sdk.set_tag("failure_type", "partial")
            sentry_sdk.capture_exception(exc)
            logger.exception("%s_%s_failed", self.provider_name(), extractor_name)
            error_str = str(exc).lower()
            if "timeout" in error_str:
                error_type = "timeout"
            elif "auth" in error_str or "401" in error_str or "403" in error_str:
                error_type = "auth"
            elif "rate" in error_str or "429" in error_str:
                error_type = "rate_limit"
            else:
                error_type = "api_error"
            return [], SubExtractorFailure(
                extractor_name=extractor_name,
                error=str(exc)[:500],
                error_type=error_type,
            )

        else:
            return result, None

    async def extract_period_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        period_type: str,
        period_start: date,
        period_end: date,
        metric_names: list[str],
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract deduplicated metrics for an entire period.

        Default: no-op (provider has no NON_AGGREGABLE metrics).
        Override in providers that have NON_AGGREGABLE metrics.

        Args:
            tenant_id: Tenant identifier.
            credentials: Provider authentication credentials.
            period_type: "weekly", "monthly", or "quarterly".
            period_start: First day of the period.
            period_end: Last day of the period.
            metric_names: NON_AGGREGABLE metric names to extract.
            stage: Funnel stage for extraction context.

        """
        return ExtractionResult()

    def has_period_extraction(self) -> bool:
        """Whether this provider supports period-level extraction."""
        return False

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
