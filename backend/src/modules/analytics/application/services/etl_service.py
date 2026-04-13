"""ETL Application Service — orchestrates extraction runs.

Provides high-level operations for the API and scheduler layers:
- run_extraction: single provider extraction for a tenant
- run_all_providers: extract from all active connections
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.orm import Session

    from src.modules.analytics.domain.period_config import TenantPeriodConfig
    from src.modules.analytics.domain.ports import ConnectionPort
    from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
    from src.modules.analytics.infrastructure.models.extraction_run_model import (
        ExtractionRunModel,
    )
    from src.modules.analytics.infrastructure.providers.base import (
        BaseMetricsProvider,
        ExtractedMetric,
    )
    from src.modules.crm.application.services.customer_service import CustomerService
    from src.modules.offer.infrastructure.repositories.external_product_mapping_repository import (
        ExternalProductMappingRepository,
    )

from sqlalchemy import select

from src.modules.analytics.application.config import ETLConfig
from src.modules.analytics.application.cost_type_mapping import get_cost_type
from src.modules.analytics.application.services.channel_registry import (
    CHANNEL_TYPE_TO_PROVIDERS,
)
from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations
from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
from src.modules.analytics.infrastructure.etl.transformers import (
    transform_staging_to_official,
)
from src.modules.analytics.infrastructure.models.staging_metrics_model import (
    StagingMetricModel,
)
from src.modules.analytics.infrastructure.providers.registry import (
    PROVIDER_REGISTRY,
    get_provider,
)
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
from src.shared.domain.datetime_utils import utc_today

logger = logging.getLogger(__name__)

# Maximum lookback for any extraction
_MAX_LOOKBACK_DAYS = ETLConfig.MAX_LOOKBACK_DAYS

# Providers that need multiple stages extracted.
# Default stage for unlisted providers is ["attraction"].
PROVIDER_STAGES: dict[str, list[str]] = {
    "shopify": ["opportunity", "sales"],
    "mailerlite": ["capture", "nurture"],
}


def _parse_shopify_line_items(line_items_raw: list[dict]) -> list[dict]:
    """Parse Shopify line_items into a normalized list of dicts."""
    return [
        {
            "product_id": str(item.get("product_id", "")),
            "variant_id": str(item.get("variant_id", "")),
            "title": item.get("title", ""),
            "price": float(item.get("price", 0)),
            "quantity": int(item.get("quantity", 1)),
        }
        for item in line_items_raw
    ]


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
    ) -> None:
        self.db = db
        self.connection_port = connection_port
        self.cache = cache

    async def run_extraction(
        self,
        tenant_id: UUID,
        provider_name: str,
        start_date: date | None = None,
        end_date: date | None = None,
        stage: str = "attraction",
    ) -> ExtractionRunModel | None:
        """Run ETL extraction for a single provider.

        For multi-stage providers (e.g. mailerlite -> capture + nurture),
        all stages defined in PROVIDER_STAGES are extracted sequentially.

        Args:
            tenant_id: The tenant to extract for.
            provider_name: Provider identifier (e.g. "meta", "google_analytics").
            start_date: Start of date range. Defaults to 30 days ago.
            end_date: End of date range. Defaults to yesterday.
            stage: Default stage for providers not in PROVIDER_STAGES.

        Returns:
            ExtractionRunModel with final status (last stage's run).
        """
        # Default date range: last 30 days
        if end_date is None:
            end_date = utc_today() - timedelta(days=1)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Enforce max lookback
        earliest = utc_today() - timedelta(days=_MAX_LOOKBACK_DAYS)
        start_date = max(start_date, earliest)

        # Multi-stage providers: iterate all stages (same as run_initial_load)
        stages = PROVIDER_STAGES.get(provider_name, [stage])

        # Resolve provider from registry
        provider = get_provider(provider_name)

        # Resolve tenant period config
        period_config = self._get_period_config(tenant_id)

        # Instantiate repositories (shared across stages)
        staging_repo = StagingMetricsRepository(self.db)
        official_repo = OfficialMetricsRepository(self.db)
        run_repo = ExtractionRunRepository(self.db)

        last_run = None
        for stg in stages:
            pipeline = ETLPipeline(
                db=self.db,
                provider=provider,
                connection_port=self.connection_port,
                staging_repo=staging_repo,
                official_repo=official_repo,
                run_repo=run_repo,
                cache=self.cache,
                period_config=period_config,
            )

            logger.info(
                "Starting ETL extraction: tenant=%s provider=%s stage=%s dates=%s to %s",
                tenant_id,
                provider_name,
                stg,
                start_date,
                end_date,
            )

            last_run = await pipeline.run(tenant_id, start_date, end_date, stage=stg)

        return last_run

    def _get_period_config(self, tenant_id: UUID) -> TenantPeriodConfig:
        """Resolve TenantPeriodConfig from the tenant's DB columns."""
        from src.modules.analytics.domain.period_config import TenantPeriodConfig
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel

        stmt = select(TenantModel).where(TenantModel.id == tenant_id)
        tenant = self.db.execute(stmt).scalar_one_or_none()
        if tenant is None:
            return TenantPeriodConfig()
        return TenantPeriodConfig(
            weekly_start_day=tenant.weekly_start_day or 0,
            fiscal_year_start_month=tenant.fiscal_year_start_month or 1,
            fiscal_year_start_day=tenant.fiscal_year_start_day or 1,
        )

    async def run_all_providers(self, tenant_id: UUID) -> list[ExtractionRunModel | None]:
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
                    provider_name,
                    tenant_id,
                    exc,
                )
            except Exception:
                logger.exception(
                    "ETL extraction failed for provider %s tenant %s",
                    provider_name,
                    tenant_id,
                )

        return results

    async def _run_provider_isolated(
        self,
        tenant_id: UUID,
        provider_name: str,
        days: int,
    ) -> dict:
        """Run run_initial_load with an isolated DB session (safe for asyncio.gather).

        Each concurrent provider gets its own Session so they don't share
        SQLAlchemy state. The MetricsCache (Redis) is shared — it's thread-safe.
        """
        from src.core.database import SessionLocal
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        db = SessionLocal()
        try:
            conn_port = ConnectionPortImpl(db)
            svc = ETLService(db, connection_port=conn_port, cache=self.cache)
            return await svc.run_initial_load(tenant_id, provider_name, days=days)
        finally:
            db.close()

    async def run_sync_all(self, tenant_id: UUID, days: int = 30) -> dict:
        """Sync all connected providers for a tenant (providers run in parallel).

        Phase 1 (sequential, shared session): resolve provider list, check cooldowns.
        Phase 2 (parallel, isolated sessions): run each provider via asyncio.gather.

        Returns aggregated result with per-provider details.
        """
        connections = await self.connection_port.list_active_connections(tenant_id)

        # Deduplicate: connection channel_types → ETL provider names
        providers_to_sync: set[str] = set()
        for conn in connections:
            etl_providers = CHANNEL_TYPE_TO_PROVIDERS.get(conn.channel_type, set())
            providers_to_sync.update(etl_providers)

        # Only keep providers that have a registered adapter
        providers_to_sync = providers_to_sync & set(PROVIDER_REGISTRY.keys())

        if not providers_to_sync:
            return {
                "status": "ok",
                "providers_synced": 0,
                "providers_skipped_cooldown": 0,
                "providers_failed": 0,
                "total_loaded": 0,
                "total_skipped": 0,
                "details": [],
            }

        # Phase 1 — cooldown check (sequential, uses shared self.db)
        run_repo = ExtractionRunRepository(self.db)
        cooldown = timedelta(minutes=15)
        now = datetime.now(UTC)

        details: list[dict] = []
        providers_to_run: list[str] = []
        skipped_cooldown = 0

        for provider_name in sorted(providers_to_sync):
            latest_run = run_repo.get_latest(tenant_id, provider_name)
            if latest_run and latest_run.started_at:
                elapsed = now - latest_run.started_at
                if elapsed < cooldown:
                    remaining = cooldown - elapsed
                    remaining_min = int(remaining.total_seconds() // 60) + 1
                    details.append(
                        {
                            "provider": provider_name,
                            "status": "skipped_cooldown",
                            "remaining_minutes": remaining_min,
                        },
                    )
                    skipped_cooldown += 1
                    continue
            providers_to_run.append(provider_name)

        # Phase 2 — parallel execution (each provider gets an isolated DB session)
        raw_results = await asyncio.gather(
            *[
                asyncio.wait_for(
                    self._run_provider_isolated(tenant_id, p, days),
                    timeout=90.0,
                )
                for p in providers_to_run
            ],
            return_exceptions=True,
        )

        total_loaded = 0
        total_skipped = 0
        synced = 0
        failed = 0

        for provider_name, result in zip(providers_to_run, raw_results, strict=False):
            if isinstance(result, Exception):
                logger.error(
                    "sync_all provider %s failed for tenant %s: %s",
                    provider_name,
                    tenant_id,
                    result,
                    exc_info=result,
                )
                details.append(
                    {
                        "provider": provider_name,
                        "status": "failed",
                        "error": str(result),
                    },
                )
                failed += 1
            else:
                details.append(
                    {
                        "provider": provider_name,
                        "status": "ok",
                        "loaded": result["loaded"],
                        "skipped": result["skipped"],
                        "total": result["total"],
                    },
                )
                total_loaded += result["loaded"]
                total_skipped += result["skipped"]
                synced += 1

        return {
            "status": "ok",
            "providers_synced": synced,
            "providers_skipped_cooldown": skipped_cooldown,
            "providers_failed": failed,
            "total_loaded": total_loaded,
            "total_skipped": total_skipped,
            "details": details,
        }

    async def run_period_extraction(
        self,
        tenant_id: UUID,
        period_type: str,
        period_start: date,
        period_end: date,
    ) -> list[dict]:
        """Extract NON_AGGREGABLE metrics for a complete period from all providers.

        Iterates through all active connections, checks which providers support
        period extraction, performs gap detection, and extracts missing periods.

        Returns list of per-provider result dicts.
        """
        from src.modules.analytics.infrastructure.etl.period_pipeline import (
            PeriodExtractionPipeline,
        )
        from src.modules.analytics.infrastructure.repositories.period_metrics_repository import (
            PeriodMetricsRepository,
        )

        connections = await self.connection_port.list_active_connections(tenant_id)
        results = []

        period_repo = PeriodMetricsRepository(self.db)
        run_repo = ExtractionRunRepository(self.db)

        for conn in connections:
            provider_name = conn.channel_type
            try:
                provider = get_provider(provider_name)
            except ValueError:
                continue

            if not provider.has_period_extraction():
                continue

            # Gap detection: skip if period already extracted
            existing = period_repo.get_existing_periods(
                tenant_id,
                provider_name,
                period_type,
                period_start,
                period_end,
            )
            if period_start in existing:
                results.append(
                    {
                        "provider": provider_name,
                        "status": "skipped",
                        "reason": "already_extracted",
                    },
                )
                continue

            pipeline = PeriodExtractionPipeline(
                db=self.db,
                provider=provider,
                connection_port=self.connection_port,
                period_repo=period_repo,
                run_repo=run_repo,
                cache=self.cache,
            )

            result = await pipeline.run(
                tenant_id=tenant_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
            )
            results.append(result)

        return results

    async def _sync_ig_dm(self, tenant_id: UUID) -> dict | None:
        """Run IG DM conversation sync as part of sync_all.

        Returns the sync result dict, or None if no Meta credentials.
        """
        from src.modules.analytics.application.services.ig_dm_sync_service import (
            InstagramDMSyncService,
        )

        sync_service = InstagramDMSyncService(
            self.db,
            connection_port=self.connection_port,
        )
        return await sync_service.sync(tenant_id)

    async def run_initial_load(
        self,
        tenant_id: UUID,
        provider_name: str,
        days: int = 30,
        stage: str = "attraction",
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> dict:
        """Load historical daily metrics, skipping days already in DB.

        For multi-stage providers (e.g. shopify -> opportunity + sales),
        all stages are extracted in a single run.

        Returns dict with total, loaded, skipped counts.
        """
        # Determine which stages to extract
        stages = PROVIDER_STAGES.get(provider_name, [stage])

        end_date = utc_today() - timedelta(days=1)
        start_date = utc_today() - timedelta(days=days)

        # Enforce max lookback
        earliest = utc_today() - timedelta(days=_MAX_LOOKBACK_DAYS)
        start_date = max(start_date, earliest)

        period_config = self._get_period_config(tenant_id)

        # Gap detection: find days already loaded
        official_repo = OfficialMetricsRepository(self.db)
        existing = official_repo.get_existing_dates(
            tenant_id,
            provider_name,
            start_date,
            end_date,
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

        # Extract daily metrics from provider (all stages)
        provider = get_provider(provider_name)
        creds = await self.connection_port.get_credentials(tenant_id, provider_name)
        provider_creds = {**creds.credentials, **creds.config}

        extracted = []
        for stg in stages:
            stage_result = await provider.extract_metrics_daily(
                tenant_id=tenant_id,
                credentials=provider_creds,
                start_date=min_missing,
                end_date=max_missing,
                stage=stg,
            )
            extracted.extend(stage_result.metrics)

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

        run = run_repo.create(
            tenant_id,
            provider_name,
            period_start=min_missing,
            period_end=max_missing,
            extraction_type="initial_load",
        )
        run_id = run.id

        self._stage_transform_upsert_aggregate(
            tenant_id,
            provider_name,
            extracted,
            run_id,
            period_config,
            staging_repo,
            official_repo,
        )

        # Create CRM records (journey_events + SaleModel) for Shopify backfill
        if provider_name == "shopify":
            crm_result = self._create_shopify_crm_records(
                tenant_id=tenant_id,
                provider=provider,
            )
            logger.info(
                "Shopify CRM backfill: orders=%d checkouts=%d sales=%d",
                crm_result["orders_processed"],
                crm_result["checkouts_processed"],
                crm_result["sales_created"],
            )

        self.db.commit()
        await self.cache.invalidate_tenant(str(tenant_id))

        loaded = len({m.date for m in extracted})

        # Step: Period extraction for NON_AGGREGABLE metrics (reach, frequency, etc.)
        await self._try_period_extraction(
            tenant_id,
            provider_name,
            start_date,
            end_date,
            run_repo,
        )

        if progress_callback:
            progress_callback(total, total, "completed")

        logger.info(
            "Initial load completed: tenant=%s provider=%s stages=%s loaded=%d skipped=%d",
            tenant_id,
            provider_name,
            stages,
            loaded,
            len(existing),
        )
        return {"total": total, "loaded": loaded, "skipped": len(existing)}

    # ------------------------------------------------------------------
    # Shopify CRM backfill helpers
    # ------------------------------------------------------------------

    def _stage_transform_upsert_aggregate(
        self,
        tenant_id: UUID,
        provider_name: str,
        extracted: list[ExtractedMetric],
        run_id: UUID,
        period_config: TenantPeriodConfig,
        staging_repo: StagingMetricsRepository,
        official_repo: OfficialMetricsRepository,
    ) -> None:
        """Stage extracted metrics, transform to official, upsert, and aggregate."""
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
        staging_repo.delete_by_tenant_provider(tenant_id, provider_name)
        staging_repo.bulk_insert(staging_models)

        official_dicts = transform_staging_to_official(
            staging_rows=staging_models,
            cost_type_fn=get_cost_type,
            extraction_run_id=run_id,
            period_config=period_config,
        )
        official_repo.upsert_from_staging(official_dicts)

        agg_dicts = compute_aggregations(
            official_rows=official_dicts,
            tenant_id=tenant_id,
            extraction_run_id=run_id,
            period_config=period_config,
        )
        if agg_dicts:
            channels_in_batch: set[str] = {a["channel_slug"] for a in agg_dicts}
            agg_repo = MetricAggregationRepository(self.db)
            for ch in channels_in_batch:
                ch_aggs = [a for a in agg_dicts if a["channel_slug"] == ch]
                agg_repo.replace_aggregations(tenant_id, ch, ch_aggs)

    def _create_shopify_crm_records(
        self,
        tenant_id: UUID,
        provider: BaseMetricsProvider,
    ) -> dict:
        """Create journey_events + SaleModel from cached Shopify orders/checkouts.

        Replicates what webhooks produce so that UnmatchedProducts and
        OfferLadder widgets work after an ETL backfill.
        """
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )
        from src.modules.offer.infrastructure.repositories.external_product_mapping_repository import (
            ExternalProductMappingRepository,
        )

        orders = provider.get_last_extracted_orders()
        checkouts = provider.get_last_extracted_checkouts()

        if not orders and not checkouts:
            logger.info("shopify_etl_crm_no_data tenant=%s", tenant_id)
            return {"orders_processed": 0, "checkouts_processed": 0, "sales_created": 0}

        customer_svc = CustomerService(self.db)
        mapping_repo = ExternalProductMappingRepository(self.db)

        # Build set of completed checkout tokens for abandoned-checkout filtering
        completed_tokens: set[str] = {str(token) for order in orders if (token := order.get("checkout_token"))}

        orders_processed, sales_created = self._process_shopify_orders(
            tenant_id,
            orders,
            customer_svc,
            mapping_repo,
        )
        checkouts_processed = self._process_shopify_checkouts(
            tenant_id,
            checkouts,
            completed_tokens,
            customer_svc,
        )

        # Flush to catch constraint violations before caller commits
        self.db.flush()

        logger.info(
            "shopify_etl_crm_records_created tenant=%s orders=%d checkouts=%d sales=%d",
            tenant_id,
            orders_processed,
            checkouts_processed,
            sales_created,
        )
        return {
            "orders_processed": orders_processed,
            "checkouts_processed": checkouts_processed,
            "sales_created": sales_created,
        }

    def _process_shopify_orders(
        self,
        tenant_id: UUID,
        orders: list[dict],
        customer_svc: CustomerService,
        mapping_repo: ExternalProductMappingRepository,
    ) -> tuple[int, int]:
        """Process completed orders into journey_events + SaleModel. Returns (orders_processed, sales_created)."""
        from sqlalchemy import func as sa_func
        from sqlalchemy import select as sa_select

        from src.modules.crm.infrastructure.models.customer_model import (
            JourneyEventModel,
        )
        from src.modules.crm.infrastructure.models.sale_model import SaleModel
        from src.shared.domain.enums import SaleStage, SaleStatus

        orders_processed = 0
        sales_created = 0

        for order in orders:
            fin_status = order.get("financial_status", "")
            if fin_status in ("voided", "refunded"):
                continue

            order_id = str(order.get("id", ""))
            if not order_id:
                continue

            # Deduplication: skip if journey_event already exists for this order
            existing_stmt = (
                sa_select(JourneyEventModel.id)
                .where(
                    JourneyEventModel.tenant_id == tenant_id,
                    JourneyEventModel.event_name == "checkout_completed",
                    sa_func.jsonb_extract_path_text(
                        JourneyEventModel.properties,
                        "order_id",
                    )
                    == order_id,
                )
                .limit(1)
            )
            if self.db.execute(existing_stmt).scalar_one_or_none():
                continue

            # Resolve email (top-level or nested in customer)
            email = order.get("email") or (order.get("customer") or {}).get("email")
            if not email:
                logger.warning("shopify_etl_order_no_email order_id=%s", order_id)
                continue

            # Resolve/create CDP profile
            customer = order.get("customer") or {}
            first_name = customer.get("first_name", "")
            last_name = customer.get("last_name", "")
            customer_name = f"{first_name} {last_name}".strip()

            profile = customer_svc.identify(
                tenant_id=tenant_id,
                traits={"email": email, "name": customer_name},
                identities={},
            )

            line_items_data = _parse_shopify_line_items(order.get("line_items", []))
            checkout_token = str(order.get("checkout_token", ""))
            total_price = float(order.get("total_price", 0))
            currency = order.get("currency", "USD")
            occurred_at = self._parse_shopify_datetime(
                order.get("processed_at") or order.get("created_at", ""),
            )

            # Create journey_event
            event = JourneyEventModel(
                profile_id=profile.id,
                tenant_id=tenant_id,
                event_name="checkout_completed",
                event_type="track",
                properties={
                    "source": "shopify",
                    "order_id": order_id,
                    "checkout_token": checkout_token,
                    "total_price": total_price,
                    "currency": currency,
                    "line_items_count": len(line_items_data),
                    "line_items": line_items_data,
                    "etl_backfill": True,
                },
                occurred_at=occurred_at,
            )
            self.db.add(event)

            # Create SaleModel per line_item
            sales_created += self._create_sales_from_line_items(
                tenant_id,
                order_id,
                profile.id,
                line_items_data,
                currency,
                occurred_at,
                mapping_repo,
                sa_select,
                SaleModel,
                SaleStage,
                SaleStatus,
            )
            orders_processed += 1

        return orders_processed, sales_created

    def _create_sales_from_line_items(
        self,
        tenant_id: UUID,
        order_id: str,
        profile_id: UUID,
        line_items_data: list[dict],
        currency: str,
        occurred_at: datetime | None,
        mapping_repo: ExternalProductMappingRepository,
        sa_select: Callable[..., object],
        SaleModel: type,  # noqa: N803
        SaleStage: type,  # noqa: N803
        SaleStatus: type,  # noqa: N803
    ) -> int:
        """Create SaleModel per line_item. Returns count of sales created."""
        product_ids = [li["product_id"] for li in line_items_data if li["product_id"]]
        resolved_mappings = mapping_repo.bulk_resolve(tenant_id, "shopify", product_ids) if product_ids else {}

        sales_created = 0
        for item in line_items_data:
            product_id = item["product_id"]
            if not product_id:
                continue

            txn_id = f"shopify-{order_id}-{product_id}"

            # Dedup by transaction_id
            existing_sale = self.db.execute(
                sa_select(SaleModel.id)
                .where(
                    SaleModel.tenant_id == tenant_id,
                    SaleModel.transaction_id == txn_id,
                )
                .limit(1),
            ).scalar_one_or_none()
            if existing_sale:
                continue

            offer_id = resolved_mappings.get(product_id)
            if not offer_id:
                continue
            line_amount = item["price"] * item["quantity"]

            sale = SaleModel(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                customer_id=profile_id,
                offer_id=offer_id,
                transaction_id=txn_id,
                amount=line_amount,
                currency=currency,
                status=SaleStatus.COMPLETED,
                stage=SaleStage.CONVERSION,
                source="SHOPIFY",
                metadata_info={"etl_backfill": True, "shopify_order_id": order_id},
                occurred_at=occurred_at,
            )
            self.db.add(sale)
            sales_created += 1

        return sales_created

    def _process_shopify_checkouts(
        self,
        tenant_id: UUID,
        checkouts: list[dict],
        completed_tokens: set[str],
        customer_svc: CustomerService,
    ) -> int:
        """Process abandoned checkouts into journey_events. Returns checkouts_processed."""
        from sqlalchemy import func as sa_func
        from sqlalchemy import select as sa_select

        from src.modules.crm.infrastructure.models.customer_model import (
            JourneyEventModel,
        )

        checkouts_processed = 0

        for checkout in checkouts:
            token = str(checkout.get("token", ""))

            # Skip completed checkouts (handled as orders above)
            if token and token in completed_tokens:
                continue

            # Deduplication
            if token:
                existing_stmt = (
                    sa_select(JourneyEventModel.id)
                    .where(
                        JourneyEventModel.tenant_id == tenant_id,
                        JourneyEventModel.event_name == "checkout_initiated",
                        sa_func.jsonb_extract_path_text(
                            JourneyEventModel.properties,
                            "checkout_token",
                        )
                        == token,
                    )
                    .limit(1)
                )
                if self.db.execute(existing_stmt).scalar_one_or_none():
                    continue

            email = checkout.get("email")
            if not email:
                continue

            billing = checkout.get("billing_address") or {}
            profile = customer_svc.identify(
                tenant_id=tenant_id,
                traits={"email": email, "name": billing.get("name", "")},
                identities={},
            )

            line_items_data = _parse_shopify_line_items(checkout.get("line_items", []))
            occurred_at = self._parse_shopify_datetime(checkout.get("created_at", ""))

            event = JourneyEventModel(
                profile_id=profile.id,
                tenant_id=tenant_id,
                event_name="checkout_initiated",
                event_type="track",
                properties={
                    "source": "shopify",
                    "checkout_token": token,
                    "total_price": float(checkout.get("total_price", 0)),
                    "currency": checkout.get("currency", "USD"),
                    "line_items_count": len(line_items_data),
                    "line_items": line_items_data,
                    "etl_backfill": True,
                },
                occurred_at=occurred_at,
            )
            self.db.add(event)
            checkouts_processed += 1

        return checkouts_processed

    async def _try_period_extraction(
        self,
        tenant_id: UUID,
        provider_name: str,
        start_date: date,
        end_date: date,
        run_repo: ExtractionRunRepository,
    ) -> None:
        """Trigger period extraction for NON_AGGREGABLE metrics (non-fatal).

        Called after the main initial_load completes. Fetches period-level
        values (e.g. reach, frequency) that cannot be summed across days.
        """
        from src.modules.analytics.infrastructure.etl.period_pipeline import (
            PeriodExtractionPipeline,
        )
        from src.modules.analytics.infrastructure.repositories.period_metrics_repository import (
            PeriodMetricsRepository,
        )

        try:
            provider = get_provider(provider_name)
            if not provider.has_period_extraction():
                return

            period_repo = PeriodMetricsRepository(self.db)
            period_pipeline = PeriodExtractionPipeline(
                db=self.db,
                provider=provider,
                connection_port=self.connection_port,
                period_repo=period_repo,
                run_repo=run_repo,
                cache=self.cache,
            )
            await period_pipeline.run(
                tenant_id=tenant_id,
                period_type="last_30_days",
                period_start=start_date,
                period_end=end_date,
            )
        except Exception as exc:  # noqa: BLE001 — service resilience
            logger.warning(
                "Period extraction failed (non-fatal): tenant=%s provider=%s error=%s",
                tenant_id,
                provider_name,
                exc,
            )

    @staticmethod
    def _parse_shopify_datetime(iso_str: str) -> datetime | None:
        """Parse Shopify ISO datetime to Python datetime."""
        if not iso_str:
            return None
        try:
            from datetime import datetime as dt

            return dt.fromisoformat(iso_str)
        except (ValueError, AttributeError):
            return None
