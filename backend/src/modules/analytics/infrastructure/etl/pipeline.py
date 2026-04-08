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
from src.modules.analytics.domain.exceptions import ConnectionRevokedException
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
        run = self.run_repo.create(tenant_id, provider_name)
        run_id = run.id
        self.run_repo.update_status(
            run_id=run_id,
            status=ExtractionStatus.RUNNING,
        )

        try:
            # Step 2: Get credentials
            creds = await self.connection_port.get_credentials(tenant_id, provider_name)

            # Step 3: Extract metrics from provider API
            # Merge config into credentials so providers have access to
            # connection-level config (e.g. shop_domain for Shopify)
            provider_creds = {**creds.credentials, **creds.config}
            result = await self.provider.extract_metrics(
                tenant_id=tenant_id,
                credentials=provider_creds,
                start_date=start_date,
                end_date=end_date,
                stage=stage,
            )
            extracted = result.metrics

            # Step 4: Convert to staging models and bulk insert
            staging_models = [
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
            self.staging_repo.delete_by_tenant_provider(tenant_id, provider_name)
            rows_staged = self.staging_repo.bulk_insert(staging_models)

            # Step 5: Transform staging -> official format
            official_dicts = transform_staging_to_official(
                staging_rows=staging_models,
                cost_type_fn=get_cost_type,
                extraction_run_id=run_id,
                stage_slug=stage,
                period_config=self.period_config,
            )

            # Step 6: Upsert official metrics
            _rows_official = self.official_repo.upsert_from_staging(official_dicts)

            # Step 7: Compute aggregations
            agg_dicts = compute_aggregations(
                official_rows=official_dicts,
                tenant_id=tenant_id,
                extraction_run_id=run_id,
                period_config=self.period_config,
            )
            if agg_dicts:
                # Group agg_dicts by channel_slug for scoped replace
                channels_in_batch: set[str] = {a["channel_slug"] for a in agg_dicts}
                agg_repo = MetricAggregationRepository(self.db)
                for ch in channels_in_batch:
                    ch_aggs = [a for a in agg_dicts if a["channel_slug"] == ch]
                    agg_repo.replace_aggregations(tenant_id, ch, ch_aggs)

            # Step 8: Determine final status based on partial failures
            duration = time.monotonic() - start_time
            if result.failures and extracted:
                final_status = ExtractionStatus.PARTIAL_SUCCESS
                final_error = None
            elif result.failures and not extracted:
                final_status = ExtractionStatus.FAILED
                final_error = "; ".join(
                    f"{f.extractor_name}: {f.error[:100]}" for f in result.failures
                )
            else:
                final_status = ExtractionStatus.SUCCESS
                final_error = None

            self.run_repo.update_status(
                run_id=run_id,
                status=final_status,
                error=final_error,
                metrics_count=len(extracted),
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

            # Commit the transaction
            self.db.commit()

            # Step 9: Invalidate cache (outside transaction — cache is best-effort)
            await self.cache.invalidate_tenant(str(tenant_id))

            logger.info(
                "ETL pipeline completed: tenant=%s provider=%s status=%s metrics=%d failures=%d duration=%.2fs",
                tenant_id,
                provider_name,
                final_status.value,
                len(extracted),
                len(result.failures),
                duration,
            )

            return run

        except ConnectionRevokedException as exc:
            # Connection revoked — mark FAILED, no retry
            self.db.rollback()
            duration = time.monotonic() - start_time
            self.run_repo.update_status(
                run_id=run_id,
                status=ExtractionStatus.FAILED,
                error=f"Connection revoked: {exc}",
                duration_seconds=round(duration, 2),
            )
            self.db.commit()
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("tenant_id", str(tenant_id))
                scope.set_tag("provider", provider_name)
                scope.set_tag("etl_run_id", str(run_id))
                scope.set_tag("failure_type", "connection_revoked")
                sentry_sdk.capture_exception(exc)
            logger.warning(
                "ETL pipeline failed (connection revoked): tenant=%s provider=%s",
                tenant_id,
                provider_name,
            )
            return run

        except Exception as exc:
            # General failure — mark FAILED, allow retry
            self.db.rollback()
            duration = time.monotonic() - start_time
            self.run_repo.update_status(
                run_id=run_id,
                status=ExtractionStatus.FAILED,
                error=str(exc),
                duration_seconds=round(duration, 2),
            )
            self.db.commit()
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("tenant_id", str(tenant_id))
                scope.set_tag("provider", provider_name)
                scope.set_tag("etl_run_id", str(run_id))
                scope.set_tag("failure_type", "general")
                sentry_sdk.capture_exception(exc)
            logger.error(
                "ETL pipeline failed: tenant=%s provider=%s error=%s",
                tenant_id,
                provider_name,
                exc,
                exc_info=True,
            )
            return run
