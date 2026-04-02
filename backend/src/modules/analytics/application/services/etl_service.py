"""ETL Application Service — orchestrates extraction runs.

Provides high-level operations for the API and scheduler layers:
- run_extraction: single provider extraction for a tenant
- run_all_providers: extract from all active connections
"""

import asyncio
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
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
from src.modules.analytics.infrastructure.providers.registry import get_provider, PROVIDER_REGISTRY
from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
    ExtractionRunRepository,
)
from src.modules.analytics.application.services.channel_registry import CHANNEL_TYPE_TO_PROVIDERS
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.analytics.infrastructure.repositories.staging_repository import (
    StagingMetricsRepository,
)

logger = logging.getLogger(__name__)

# Providers that need multiple stages extracted.
# Default stage for unlisted providers is ["attraction"].
PROVIDER_STAGES: dict[str, list[str]] = {
    "shopify": ["opportunity", "sales"],
    "mailerlite": ["capture", "nurture"],
}


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

    async def run_sync_all(self, tenant_id: UUID, days: int = 30) -> dict:
        """Sync all connected providers for a tenant.

        For each active connection, resolves the ETL provider(s) via
        CHANNEL_TYPE_TO_PROVIDERS, deduplicates, checks cooldown, and
        runs run_initial_load (gap-detection — fast when no gaps).

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

        run_repo = ExtractionRunRepository(self.db)
        cooldown = timedelta(minutes=15)
        now = datetime.now(timezone.utc)

        details: list[dict] = []
        total_loaded = 0
        total_skipped = 0
        synced = 0
        skipped_cooldown = 0
        failed = 0

        for provider_name in sorted(providers_to_sync):
            # Check cooldown
            latest_run = run_repo.get_latest(tenant_id, provider_name)
            if latest_run and latest_run.started_at:
                elapsed = now - latest_run.started_at
                if elapsed < cooldown:
                    remaining = cooldown - elapsed
                    remaining_min = int(remaining.total_seconds() // 60) + 1
                    details.append({
                        "provider": provider_name,
                        "status": "skipped_cooldown",
                        "remaining_minutes": remaining_min,
                    })
                    skipped_cooldown += 1
                    continue

            try:
                result = await asyncio.wait_for(
                    self.run_initial_load(tenant_id, provider_name, days=days),
                    timeout=90.0,
                )
                details.append({
                    "provider": provider_name,
                    "status": "ok",
                    "loaded": result["loaded"],
                    "skipped": result["skipped"],
                    "total": result["total"],
                })
                total_loaded += result["loaded"]
                total_skipped += result["skipped"]
                synced += 1
            except Exception as exc:
                logger.error(
                    "sync_all provider %s failed for tenant %s: %s",
                    provider_name, tenant_id, exc,
                    exc_info=True,
                )
                details.append({
                    "provider": provider_name,
                    "status": "failed",
                    "error": str(exc),
                })
                failed += 1

        return {
            "status": "ok",
            "providers_synced": synced,
            "providers_skipped_cooldown": skipped_cooldown,
            "providers_failed": failed,
            "total_loaded": total_loaded,
            "total_skipped": total_skipped,
            "details": details,
        }

    async def _sync_ig_dm(self, tenant_id: UUID) -> dict | None:
        """Run IG DM conversation sync as part of sync_all.

        Returns the sync result dict, or None if no Meta credentials.
        """
        from src.modules.analytics.application.services.ig_dm_sync_service import (
            InstagramDMSyncService,
        )

        sync_service = InstagramDMSyncService(self.db, connection_port=self.connection_port)
        return await sync_service.sync(tenant_id)

    async def run_initial_load(
        self,
        tenant_id: UUID,
        provider_name: str,
        days: int = 30,
        stage: str = "attraction",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> dict:
        """Load historical daily metrics, skipping days already in DB.

        For multi-stage providers (e.g. shopify -> opportunity + sales),
        all stages are extracted in a single run.

        Returns dict with total, loaded, skipped counts.
        """
        # Determine which stages to extract
        stages = PROVIDER_STAGES.get(provider_name, [stage])

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
        if progress_callback:
            progress_callback(total, total, "completed")

        logger.info(
            "Initial load completed: tenant=%s provider=%s stages=%s loaded=%d skipped=%d",
            tenant_id, provider_name, stages, loaded, len(existing),
        )
        return {"total": total, "loaded": loaded, "skipped": len(existing)}

    # ------------------------------------------------------------------
    # Shopify CRM backfill helpers
    # ------------------------------------------------------------------

    def _create_shopify_crm_records(
        self,
        tenant_id: UUID,
        provider,
    ) -> dict:
        """Create journey_events + SaleModel from cached Shopify orders/checkouts.

        Replicates what webhooks produce so that UnmatchedProducts and
        OfferLadder widgets work after an ETL backfill.
        """
        from sqlalchemy import select as sa_select, func as sa_func
        from src.modules.crm.application.services.customer_service import CustomerService
        from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel
        from src.modules.crm.infrastructure.models.sale_model import SaleModel
        from src.modules.crm.domain.enums import SaleStatus, SaleStage
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
        completed_tokens: set[str] = set()
        for order in orders:
            token = order.get("checkout_token")
            if token:
                completed_tokens.add(str(token))

        orders_processed = 0
        checkouts_processed = 0
        sales_created = 0

        # --- Completed orders → checkout_completed + SaleModel ---
        for order in orders:
            fin_status = order.get("financial_status", "")
            if fin_status in ("voided", "refunded"):
                continue

            order_id = str(order.get("id", ""))
            if not order_id:
                continue

            # Deduplication: skip if journey_event already exists for this order
            existing_stmt = sa_select(JourneyEventModel.id).where(
                JourneyEventModel.tenant_id == tenant_id,
                JourneyEventModel.event_name == "checkout_completed",
                sa_func.jsonb_extract_path_text(
                    JourneyEventModel.properties, "order_id"
                ) == order_id,
            ).limit(1)
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

            # Extract line items (same structure as webhook)
            line_items_raw = order.get("line_items", [])
            line_items_data = [
                {
                    "product_id": str(item.get("product_id", "")),
                    "variant_id": str(item.get("variant_id", "")),
                    "title": item.get("title", ""),
                    "price": float(item.get("price", 0)),
                    "quantity": int(item.get("quantity", 1)),
                }
                for item in line_items_raw
            ]

            checkout_token = str(order.get("checkout_token", ""))
            total_price = float(order.get("total_price", 0))
            currency = order.get("currency", "USD")
            occurred_at = self._parse_shopify_datetime(
                order.get("processed_at") or order.get("created_at", "")
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

            # Bulk resolve product → offer mappings
            product_ids = [li["product_id"] for li in line_items_data if li["product_id"]]
            resolved_mappings = (
                mapping_repo.bulk_resolve(tenant_id, "shopify", product_ids)
                if product_ids
                else {}
            )

            # Create SaleModel per line_item (direct — no SaleCompletedEvent)
            for item in line_items_data:
                product_id = item["product_id"]
                if not product_id:
                    continue

                txn_id = f"shopify-{order_id}-{product_id}"

                # Dedup by transaction_id
                existing_sale = self.db.execute(
                    sa_select(SaleModel.id).where(
                        SaleModel.tenant_id == tenant_id,
                        SaleModel.transaction_id == txn_id,
                    ).limit(1)
                ).scalar_one_or_none()
                if existing_sale:
                    continue

                offer_id = resolved_mappings.get(product_id)
                if not offer_id:
                    # No product→offer mapping — skip SaleModel (FK requires valid offer)
                    continue
                line_amount = item["price"] * item["quantity"]

                sale = SaleModel(
                    id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    customer_id=profile.id,
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

            orders_processed += 1

        # --- Abandoned checkouts → checkout_initiated ---
        for checkout in checkouts:
            token = str(checkout.get("token", ""))

            # Skip completed checkouts (handled as orders above)
            if token and token in completed_tokens:
                continue

            # Deduplication
            if token:
                existing_stmt = sa_select(JourneyEventModel.id).where(
                    JourneyEventModel.tenant_id == tenant_id,
                    JourneyEventModel.event_name == "checkout_initiated",
                    sa_func.jsonb_extract_path_text(
                        JourneyEventModel.properties, "checkout_token"
                    ) == token,
                ).limit(1)
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

            line_items_raw = checkout.get("line_items", [])
            line_items_data = [
                {
                    "product_id": str(item.get("product_id", "")),
                    "variant_id": str(item.get("variant_id", "")),
                    "title": item.get("title", ""),
                    "price": float(item.get("price", 0)),
                    "quantity": int(item.get("quantity", 1)),
                }
                for item in line_items_raw
            ]

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

        # Flush to catch constraint violations before caller commits
        self.db.flush()

        logger.info(
            "shopify_etl_crm_records_created tenant=%s orders=%d checkouts=%d sales=%d",
            tenant_id, orders_processed, checkouts_processed, sales_created,
        )
        return {
            "orders_processed": orders_processed,
            "checkouts_processed": checkouts_processed,
            "sales_created": sales_created,
        }

    @staticmethod
    def _parse_shopify_datetime(iso_str: str):
        """Parse Shopify ISO datetime to Python datetime."""
        if not iso_str:
            return None
        try:
            from datetime import datetime as dt
            return dt.fromisoformat(iso_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
