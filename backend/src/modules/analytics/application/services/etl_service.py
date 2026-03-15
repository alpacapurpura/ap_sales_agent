"""ETL Application Service — orchestrates extraction runs.

Provides high-level operations for the API and scheduler layers:
- run_extraction: single provider extraction for a tenant
- run_all_providers: extract from all active connections
"""

import logging
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
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

        return await pipeline.run(tenant_id, start_date, end_date)

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
