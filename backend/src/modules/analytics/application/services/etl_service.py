"""ETL Application Service — orchestrates extraction runs.

Provides high-level operations for the API and scheduler layers:
- run_extraction: single provider extraction for a tenant
- run_all_providers: extract from all active connections
"""

import logging
import uuid
from datetime import date, timedelta
from typing import Callable, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
from src.modules.analytics.application.cost_type_mapping import get_cost_type
from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations
from src.modules.analytics.infrastructure.etl.transformers import (
    transform_staging_to_official,
)
from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
    MetricAggregationModel,
)
from src.modules.analytics.infrastructure.models.staging_metrics_model import (
    StagingMetricModel,
)
from src.modules.analytics.infrastructure.providers.registry import get_provider
from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
    ExtractionRunRepository,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.analytics.infrastructure.repositories.staging_repository import (
    StagingMetricsRepository,
)

logger = logging.getLogger(__name__)


class ETLService:
    """Application-level orchestration for ETL extractions.

    Wires together the provider registry, repositories, cache,
    and pipeline for use by API endpoints and background workers.
    """

    def __init__(
        self,
        db: Session,
        connection_port: ConnectionPort,
        cache: MetricsCache,
    ):
        self.db = db
        self.connection_port = connection_port
        self.cache = cache

    async def run_extraction(
        self,
        tenant_id: UUID,
        provider_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        stage: str = "attraction",
    ):
        """Run ETL extraction for a single provider.

        Args:
            tenant_id: The tenant to extract for.
            provider_name: Provider identifier (e.g. "meta", "google_analytics").
            start_date: Start of date range. Defaults to 30 days ago.
            end_date: End of date range. Defaults to yesterday.

        Returns:
            ExtractionRunModel with final status.
        """
        # Default date range: last 30 days
        if end_date is None:
            end_date = date.today() - timedelta(days=1)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Resolve provider from registry
        provider = get_provider(provider_name)

        # Instantiate repositories
        staging_repo = StagingMetricsRepository(self.db)
        official_repo = OfficialMetricsRepository(self.db)
        run_repo = ExtractionRunRepository(self.db)

        # Build and run pipeline
        pipeline = ETLPipeline(
            db=self.db,
            provider=provider,
            connection_port=self.connection_port,
            staging_repo=staging_repo,
            official_repo=official_repo,
            run_repo=run_repo,
            cache=self.cache,
        )

        logger.info(
            "Starting ETL extraction: tenant=%s provider=%s dates=%s to %s",
            tenant_id, provider_name, start_date, end_date,
        )

        return await pipeline.run(tenant_id, start_date, end_date, stage=stage)

    async def run_all_providers(self, tenant_id: UUID):
        """Run ETL extraction for all active provider connections.

        Iterates through the tenant's active connections and runs
        extraction for each provider that has a registered adapter.

        Returns:
            List of ExtractionRunModel results.
        """
        connections = await self.connection_port.list_active_connections(tenant_id)
        results = []

        for conn in connections:
            provider_name = conn.channel_type
            try:
                result = await self.run_extraction(tenant_id, provider_name)
                results.append(result)
            except ValueError as exc:
                # Provider not registered — skip
                logger.warning(
                    "Skipping unregistered provider %s for tenant %s: %s",
                    provider_name, tenant_id, exc,
                )
            except Exception as exc:
                logger.error(
                    "ETL extraction failed for provider %s tenant %s: %s",
                    provider_name, tenant_id, exc,
                    exc_info=True,
                )

        return results

    async def run_initial_load(
        self,
        tenant_id: UUID,
        provider_name: str,
        days: int = 30,
        stage: str = "attraction",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict:
        """Load historical daily metrics, skipping days already in DB.

        Returns dict with total, loaded, skipped counts.
        """
        end_date = date.today() - timedelta(days=1)
        start_date = date.today() - timedelta(days=days)

        # Gap detection: find days already loaded
        official_repo = OfficialMetricsRepository(self.db)
        existing = official_repo.get_existing_dates(
            tenant_id, provider_name, start_date, end_date
        )
        all_days = {start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)}
        missing_days = all_days - existing

        total = len(all_days)
        if not missing_days:
            if progress_callback:
                progress_callback(total, total, "completed")
            return {"total": total, "loaded": 0, "skipped": len(existing)}

        min_missing = min(missing_days)
        max_missing = max(missing_days)

        if progress_callback:
            progress_callback(0, total, "extracting")

        # Extract daily metrics from provider
        provider = get_provider(provider_name)
        creds = await self.connection_port.get_credentials(tenant_id, provider_name)
        provider_creds = {**creds.credentials, **creds.config}
        extracted = await provider.extract_metrics_daily(
            tenant_id=tenant_id,
            credentials=provider_creds,
            start_date=min_missing,
            end_date=max_missing,
            stage=stage,
        )

        # Filter to only missing days
        extracted = [m for m in extracted if m.date in missing_days]

        if not extracted:
            if progress_callback:
                progress_callback(total, total, "completed")
            return {"total": total, "loaded": 0, "skipped": len(existing)}

        if progress_callback:
            progress_callback(len(existing), total, "loading")

        # Run through staging → transform → upsert → aggregate pipeline
        staging_repo = StagingMetricsRepository(self.db)
        run_repo = ExtractionRunRepository(self.db)

        run = run_repo.create(tenant_id, provider_name)
        run_id = run.id

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
        staging_repo.bulk_insert(staging_models)

        official_dicts = transform_staging_to_official(
            staging_rows=staging_models,
            cost_type_fn=get_cost_type,
            extraction_run_id=run_id,
        )
        official_repo.upsert_from_staging(official_dicts)

        agg_dicts = compute_aggregations(
            official_rows=official_dicts,
            tenant_id=tenant_id,
            extraction_run_id=run_id,
        )
        if agg_dicts:
            agg_models = [
                MetricAggregationModel(
                    id=uuid.uuid4(),
                    tenant_id=agg["tenant_id"],
                    channel_slug=agg["channel_slug"],
                    metric_name=agg["metric_name"],
                    period_type=agg["period_type"],
                    period_start=agg["period_start"],
                    period_end=agg["period_end"],
                    value=agg["value"],
                    unit=agg["unit"],
                    currency=agg.get("currency"),
                    cost_type=agg.get("cost_type"),
                    extraction_run_id=agg.get("extraction_run_id"),
                )
                for agg in agg_dicts
            ]
            self.db.add_all(agg_models)

        self.db.commit()
        await self.cache.invalidate_tenant(str(tenant_id))

        loaded = len({m.date for m in extracted})
        if progress_callback:
            progress_callback(total, total, "completed")

        logger.info(
            "Initial load completed: tenant=%s provider=%s loaded=%d skipped=%d",
            tenant_id, provider_name, loaded, len(existing),
        )
        return {"total": total, "loaded": loaded, "skipped": len(existing)}
