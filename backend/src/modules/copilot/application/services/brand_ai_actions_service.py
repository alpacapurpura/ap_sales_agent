from typing import Literal, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.brand.application.extraction_service import BrandExtractionService
from src.modules.brand.domain.aggregates import BrandSettings
from src.modules.brand.domain.identity import BrandVisuals


class CopilotBrandAIActionsService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.brand_extraction_service = BrandExtractionService(db, tenant_id)

    async def extract_brand_identity(self, url: str, extraction_type: Literal["brand_identity"]) -> BrandVisuals:
        if extraction_type != "brand_identity":
            raise ValueError(f"Unsupported extraction type: {extraction_type}")
        return await self.brand_extraction_service.extract_visuals_only(url)

    async def extract_full_brand(
        self,
        url: Optional[str] = None,
        text: Optional[str] = None,
        mode: Literal["initial", "update"] = "initial",
        update_instructions: Optional[str] = None,
        dry_run: bool = False,
        include_visuals: bool = False,
        progress_callback=None,
    ) -> BrandSettings:
        return await self.brand_extraction_service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            progress_callback=progress_callback,
        )
