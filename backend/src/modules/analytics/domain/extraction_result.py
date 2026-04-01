"""ExtractionResult value object — carries metrics + partial failure info.

Used as the return type of BaseMetricsProvider.extract_metrics() so that
pipelines can distinguish full success, partial success, and total failure.
"""

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.analytics.infrastructure.providers.base import ExtractedMetric


@dataclass
class SubExtractorFailure:
    """Records a single sub-extractor failure within a provider run."""

    extractor_name: str   # e.g. "instagram_organic", "meta_ads"
    error: str            # str(exc)[:500]
    error_type: str       # "api_error" | "timeout" | "auth" | "rate_limit" | "unknown"


@dataclass
class ExtractionResult:
    """Result of a provider extraction: successful metrics + any partial failures."""

    metrics: List["ExtractedMetric"] = field(default_factory=list)
    failures: List[SubExtractorFailure] = field(default_factory=list)

    @property
    def has_partial_failures(self) -> bool:
        return len(self.failures) > 0 and len(self.metrics) > 0
