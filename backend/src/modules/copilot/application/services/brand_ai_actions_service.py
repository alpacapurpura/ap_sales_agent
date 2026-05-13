"""Brand AI actions service for copilot."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from luana_core_brand_studio.application.extraction_service import BrandExtractionService

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from luana_core_brand_studio.application.extraction_trace import ExtractionTraceCollector
    from luana_core_brand_studio.domain.aggregates import BrandSettings
    from luana_core_brand_studio.domain.identity import BrandVisuals
    from sqlalchemy.orm import Session


class CopilotBrandAIActionsService:
    """Service for copilot brand a i actions operations."""

    def __init__(self, db: Session, tenant_id: UUID) -> None:
        """Initialize copilot brand a i actions service."""
        self.db = db
        self.tenant_id = tenant_id
        self.brand_extraction_service = BrandExtractionService(db, tenant_id)

    async def extract_brand_identity(
        self,
        url: str,
        extraction_type: Literal["brand_identity"],
    ) -> BrandVisuals:
        """Extract brand identity."""
        if extraction_type != "brand_identity":
            msg = f"Unsupported extraction type: {extraction_type}"
            raise ValueError(msg)
        return await self.brand_extraction_service.extract_visuals_only(url)

    async def extract_full_brand(
        self,
        url: str | None = None,
        text: str | None = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: str | None = None,
        dry_run: bool = False,
        include_visuals: bool = False,
        include_assets: bool = False,
        progress_callback: Callable[[int, str], None] | None = None,
        trace: ExtractionTraceCollector | None = None,
    ) -> BrandSettings:
        """Extract full brand."""
        return await self.brand_extraction_service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            include_assets=include_assets,
            progress_callback=progress_callback,
            trace=trace,
        )
