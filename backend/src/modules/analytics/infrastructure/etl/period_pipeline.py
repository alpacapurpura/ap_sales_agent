"""Period Extraction Pipeline — extracts NON_AGGREGABLE metrics for entire periods.

Unlike the daily ETL pipeline, this pipeline:
1. Only extracts NON_AGGREGABLE metrics (reach, users, frequency, etc.)
2. Stores results in the `period_metrics` table (not `official_metrics`)
3. Uses provider-specific period APIs (Meta period=week, GA4 date range, etc.)
"""

import time
from datetime import date
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from src.modules.analytics.application.cost_type_mapping import get_cost_type
from src.modules.analytics.domain.enums import ExtractionStatus
from src.modules.analytics.domain.exceptions import ConnectionRevokedException
from src.modules.analytics.domain.metric_catalog import get_non_aggregable_for_provider
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.providers.base import BaseMetricsProvider
from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
    ExtractionRunRepository,
)
from src.modules.analytics.infrastructure.repositories.period_metrics_repository import (
    PeriodMetricsRepository,
)

logger = structlog.get_logger(__name__)


class PeriodExtractionPipeline:
    """Orchestrates period-level extraction for NON_AGGREGABLE metrics."""

    def __init__(
        self,
        db: Session,
        provider: BaseMetricsProvider,
        connection_port: ConnectionPort,
        period_repo: PeriodMetricsRepository,
        run_repo: ExtractionRunRepository,
        cache: MetricsCache,
    ):
        self.db = db
        self.provider = provider
        self.connection_port = connection_port
        self.period_repo = period_repo
        self.run_repo = run_repo
        self.cache = cache

    async def run(
        self,
        tenant_id: UUID,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> dict:
        """Execute period extraction for a single provider.

        Returns dict with status and metrics count.
        """
        provider_name = self.provider.provider_name()
        start_time = time.monotonic()

        # Determine NON_AGGREGABLE metrics for this provider
        metric_names = get_non_aggregable_for_provider(provider_name)
        if not metric_names:
            return {
                "provider": provider_name,
                "status": "skipped",
                "reason": "no_non_aggregable_metrics",
            }

        # Create extraction run with period metadata up-front
        run = self.run_repo.create(
            tenant_id,
            provider_name,
            period_start=period_start,
            period_end=period_end,
            extraction_type="period",
        )
        run_id = run.id

        # Transition status PENDING -> RUNNING (metadata already persisted)
        from sqlalchemy import update

        from src.modules.analytics.infrastructure.models.extraction_run_model import (
            ExtractionRunModel,
        )

        self.db.execute(
            update(ExtractionRunModel)
            .where(ExtractionRunModel.id == run_id)
            .values(status=ExtractionStatus.RUNNING.value)
        )

        # Commit the run row + RUNNING status NOW so it survives any later
        # rollback in the except handlers below. Without this commit, a
        # failure inside the try block triggers `db.rollback()` which wipes
        # the still-uncommitted run row, and the subsequent update_status
        # call raises "ExtractionRun not found" instead of recording the
        # real failure reason.
        self.db.commit()

        try:
            # Get credentials
            creds = await self.connection_port.get_credentials(tenant_id, provider_name)
            provider_creds = {**creds.credentials, **creds.config}

            # Extract period metrics
            result = await self.provider.extract_period_metrics(
                tenant_id=tenant_id,
                credentials=provider_creds,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                metric_names=metric_names,
            )

            # Convert to period_metrics dicts and upsert
            period_dicts = []
            for m in result.metrics:
                cost_type = get_cost_type(m.channel_slug, "attraction")
                period_dicts.append(
                    {
                        "tenant_id": tenant_id,
                        "provider": m.provider,
                        "channel_slug": m.channel_slug,
                        "metric_name": m.metric_name,
                        "value": m.value,
                        "unit": m.unit,
                        "currency": m.currency,
                        "period_type": period_type,
                        "period_start": period_start,
                        "period_end": period_end,
                        "campaign_id": m.campaign_id,
                        "ad_set_id": m.ad_set_id,
                        "ad_id": m.ad_id,
                        "cost_type": cost_type.value
                        if hasattr(cost_type, "value")
                        else cost_type,
                        "extra": m.extra,
                        "source_extraction_run_id": run_id,
                    }
                )

            rows_upserted = self.period_repo.upsert_period_metrics(period_dicts)

            # Update extraction run
            duration = time.monotonic() - start_time
            final_status = (
                ExtractionStatus.PARTIAL_SUCCESS
                if result.failures and result.metrics
                else ExtractionStatus.FAILED
                if result.failures and not result.metrics
                else ExtractionStatus.SUCCESS
            )

            self.run_repo.update_status(
                run_id=run_id,
                status=final_status,
                metrics_count=len(result.metrics),
                rows_extracted=rows_upserted,
                duration_seconds=round(duration, 2),
            )

            self.db.commit()
            await self.cache.invalidate_tenant(str(tenant_id))

            logger.info(
                "Period extraction completed: tenant=%s provider=%s period=%s %s→%s metrics=%d",
                tenant_id,
                provider_name,
                period_type,
                period_start,
                period_end,
                len(result.metrics),
            )

            return {
                "provider": provider_name,
                "status": final_status.value,
                "metrics_count": len(result.metrics),
                "period_type": period_type,
            }

        except ConnectionRevokedException as exc:
            self.db.rollback()
            duration = time.monotonic() - start_time
            self.run_repo.update_status(
                run_id=run_id,
                status=ExtractionStatus.FAILED,
                error=f"Connection revoked: {exc}",
                duration_seconds=round(duration, 2),
            )
            self.db.commit()
            logger.warning(
                "Period extraction failed (revoked): tenant=%s provider=%s",
                tenant_id,
                provider_name,
            )
            return {"provider": provider_name, "status": "revoked", "error": str(exc)}

        except Exception as exc:
            self.db.rollback()
            duration = time.monotonic() - start_time
            self.run_repo.update_status(
                run_id=run_id,
                status=ExtractionStatus.FAILED,
                error=str(exc)[:500],
                duration_seconds=round(duration, 2),
            )
            self.db.commit()
            logger.error(
                "Period extraction failed: tenant=%s provider=%s error=%s",
                tenant_id,
                provider_name,
                exc,
                exc_info=True,
            )
            return {"provider": provider_name, "status": "failed", "error": str(exc)}
