"""ETL Pipeline — orchestrates the full extraction flow atomically.

Sequence: extract -> stage -> transform -> official -> aggregate -> cache invalidate.
All DB operations run in a single transaction. On failure, everything rolls back.
"""

import time
import uuid
from datetime import date
from uuid import UUID

import sentry_sdk
import structlog
from sqlalchemy.orm import Session

from src.modules.analytics.application.cost_type_mapping import get_cost_type
from src.modules.analytics.domain.enums import ExtractionStatus
from src.modules.analytics.domain.exceptions import ConnectionRevokedError
from src.modules.analytics.domain.period_config import TenantPeriodConfig
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.etl.aggregations import (
    compute_aggregations,
)
from src.modules.analytics.infrastructure.etl.transformers import (
    transform_staging_to_official,
)
from src.modules.analytics.infrastructure.models.metric_aggregation_model import (  # noqa: F401
    MetricAggregationModel,
)
from src.modules.analytics.infrastructure.models.staging_metrics_model import (
    StagingMetricModel,
)
from src.modules.analytics.infrastructure.providers.base import BaseMetricsProvider
from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
    ExtractionRunRepository,
)
from src.modules.analytics.infrastructure.repositories.metric_aggregation_repository import (
    MetricAggregationRepository,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.analytics.infrastructure.repositories.staging_repository import (
    StagingMetricsRepository,
)

logger = structlog.get_logger(__name__)


def _build_staging_models(
    extracted: list,
    tenant_id: UUID,
    run_id: UUID,
) -> list[StagingMetricModel]:
    """Convert ExtractedMetric list to StagingMetricModel list."""
    return [
        StagingMetricModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            provider=m.provider,
            channel_slug=m.channel_slug,
            metric_name=m.metric_name,
            value=m.value,
            unit=m.unit,
            currency=m.currency,
            metric_date=m.date,
            campaign_id=m.campaign_id,
            ad_set_id=m.ad_set_id,
            ad_id=m.ad_id,
            extra=m.extra,
            extraction_run_id=run_id,
        )
        for m in extracted
    ]


def _determine_status(result) -> ExtractionStatus:
    """Determine final extraction status from result."""
    if result.failures and result.metrics:
        return ExtractionStatus.PARTIAL_SUCCESS
    if result.failures and not result.metrics:
        return ExtractionStatus.FAILED
    return ExtractionStatus.SUCCESS


class ETLPipeline:
    """Orchestrates the full ETL extraction flow for a single provider.

    The pipeline is atomic: all DB operations succeed together or
    roll back together. Cache invalidation only happens on success.
    """

    def __init__(
        self,
        db: Session,
        provider: BaseMetricsProvider,
        connection_port: ConnectionPort,
        staging_repo: StagingMetricsRepository,
        official_repo: OfficialMetricsRepository,
        run_repo: ExtractionRunRepository,
        cache: MetricsCache,
        period_config: TenantPeriodConfig | None = None,
    ):
        self.db = db
        self.provider = provider
        self.connection_port = connection_port
        self.staging_repo = staging_repo
        self.official_repo = official_repo
        self.run_repo = run_repo
        self.cache = cache
        self.period_config = period_config or TenantPeriodConfig()

    async def run(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ):
        """Execute the full ETL pipeline for a tenant and date range.

        Steps:
        1. Create ExtractionRun (PENDING -> RUNNING)
        2. Get credentials via ConnectionPort
        3. Extract metrics via provider
        4. Stage extracted metrics
        5. Transform staging -> official
        6. Upsert official metrics
        7. Compute aggregations
        8. Update ExtractionRun to SUCCESS
        9. Invalidate tenant cache

        On error: rollback DB, mark run FAILED.

        Returns:
            ExtractionRunModel with final status.
        """
        provider_name = self.provider.provider_name()
        start_time = time.monotonic()

        # Step 1: Create extraction run
        run = self.run_repo.create(
            tenant_id,
            provider_name,
            period_start=start_date,
            period_end=end_date,
            extraction_type="scheduled",
        )
        run_id = run.id
        self.run_repo.update_status(
            run_id=run_id,
            status=ExtractionStatus.RUNNING,
        )

        # Commit the run row + RUNNING status NOW so it survives any later
        # rollback in the except handlers below. Without this commit, a
        # failure inside the try block triggers `db.rollback()` which wipes
        # the still-uncommitted run row, and the subsequent update_status
        # call raises "ExtractionRun not found" instead of recording the
        # real failure reason.
        self.db.commit()

        try:
            # Steps 2-7: Extract, stage, transform, upsert, aggregate
            result, rows_staged = await self._extract_and_load(
                tenant_id,
                provider_name,
                start_date,
                end_date,
                stage,
                run_id,
            )

            # Step 8: Determine final status and record it
            duration = time.monotonic() - start_time
            self._record_run_result(
                run_id,
                result,
                rows_staged,
                duration,
            )

            self.db.commit()

            # Step 9: Invalidate cache (outside transaction — cache is best-effort)
            await self.cache.invalidate_tenant(str(tenant_id))

            final_status = _determine_status(result)
            logger.info(
                "ETL pipeline completed: tenant=%s provider=%s status=%s metrics=%d failures=%d duration=%.2fs",
                tenant_id,
                provider_name,
                final_status.value,
                len(result.metrics),
                len(result.failures),
                duration,
            )

        except ConnectionRevokedError as exc:
            self._handle_pipeline_failure(
                run_id,
                start_time,
                tenant_id,
                provider_name,
                f"Connection revoked: {exc}",
                "connection_revoked",
                exc,
                log_level="warning",
            )
            return run

        except Exception as exc:  # noqa: BLE001 — ETL pipeline resilience
            self._handle_pipeline_failure(
                run_id,
                start_time,
                tenant_id,
                provider_name,
                str(exc),
                "general",
                exc,
                log_level="error",
            )
            return run

        else:
            return run

    async def _extract_and_load(
        self,
        tenant_id,
        provider_name,
        start_date,
        end_date,
        stage,
        run_id,
    ):
        """Steps 2-7: Extract, stage, transform, upsert, aggregate. Returns (result, rows_staged)."""
        creds = await self.connection_port.get_credentials(tenant_id, provider_name)
        provider_creds = {**creds.credentials, **creds.config}
        result = await self.provider.extract_metrics(
            tenant_id=tenant_id,
            credentials=provider_creds,
            start_date=start_date,
            end_date=end_date,
            stage=stage,
        )

        staging_models = _build_staging_models(
            result.metrics,
            tenant_id,
            run_id,
        )
        self.staging_repo.delete_by_tenant_provider(tenant_id, provider_name)
        rows_staged = self.staging_repo.bulk_insert(staging_models)

        official_dicts = transform_staging_to_official(
            staging_rows=staging_models,
            cost_type_fn=get_cost_type,
            extraction_run_id=run_id,
            stage_slug=stage,
            period_config=self.period_config,
        )
        self.official_repo.upsert_from_staging(official_dicts)

        agg_dicts = compute_aggregations(
            official_rows=official_dicts,
            tenant_id=tenant_id,
            extraction_run_id=run_id,
            period_config=self.period_config,
        )
        if agg_dicts:
            channels_in_batch: set[str] = {a["channel_slug"] for a in agg_dicts}
            agg_repo = MetricAggregationRepository(self.db)
            for ch in channels_in_batch:
                ch_aggs = [a for a in agg_dicts if a["channel_slug"] == ch]
                agg_repo.replace_aggregations(tenant_id, ch, ch_aggs)

        return result, rows_staged

    def _record_run_result(self, run_id, result, rows_staged, duration):
        """Determine final status from extraction result and update the run."""
        final_status = _determine_status(result)
        final_error = None
        if result.failures and not result.metrics:
            final_error = "; ".join(
                f"{f.extractor_name}: {f.error[:100]}" for f in result.failures
            )

        self.run_repo.update_status(
            run_id=run_id,
            status=final_status,
            error=final_error,
            metrics_count=len(result.metrics),
            rows_extracted=rows_staged,
            duration_seconds=round(duration, 2),
            sub_extractor_failures=[
                {
                    "extractor_name": f.extractor_name,
                    "error": f.error,
                    "error_type": f.error_type,
                }
                for f in result.failures
            ]
            if result.failures
            else None,
        )

    def _handle_pipeline_failure(
        self,
        run_id,
        start_time,
        tenant_id,
        provider_name,
        error_msg,
        failure_type,
        exc,
        *,
        log_level="error",
    ):
        """Rollback, record failure, report to Sentry."""
        self.db.rollback()
        duration = time.monotonic() - start_time
        self.run_repo.update_status(
            run_id=run_id,
            status=ExtractionStatus.FAILED,
            error=error_msg,
            duration_seconds=round(duration, 2),
        )
        self.db.commit()
        with sentry_sdk.push_scope() as scope:
            scope.set_tag("tenant_id", str(tenant_id))
            scope.set_tag("provider", provider_name)
            scope.set_tag("etl_run_id", str(run_id))
            scope.set_tag("failure_type", failure_type)
            sentry_sdk.capture_exception(exc)
        if log_level == "warning":
            logger.warning(
                "ETL pipeline failed (%s): tenant=%s provider=%s",
                failure_type,
                tenant_id,
                provider_name,
            )
        else:
            logger.exception(
                "ETL pipeline failed: tenant=%s provider=%s error=%s",
                tenant_id,
                provider_name,
                exc,
            )
