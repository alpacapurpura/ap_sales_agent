from typing import Dict, Any, Optional, Union
import structlog
from src.modules.assets.domain.entity import Asset
from src.modules.assets.domain.enums import AssetType

logger = structlog.get_logger()


class AssetProcessor:
    def __init__(self):
        pass

    async def process_asset(self, asset: Asset, file_data: Union[bytes, str]) -> Dict[str, Any]:
        """
        Process asset to extract AI metadata.
        file_data can be raw bytes (from R2/cloud) or a local filesystem path (legacy).
        """
        if asset.type == AssetType.IMAGE:
            return await self._analyze_image(file_data, asset.user_description)

        # Future: Video/Audio processing
        return {}

    async def _analyze_image(self, file_data: Union[bytes, str], context: Optional[str]) -> Dict[str, Any]:
        try:
            from src.shared.infrastructure.files.image_analysis import ImageAnalysisService

            service = ImageAnalysisService()
            result = await service.analyze(file_data, user_context=context or "")

            return {
                "ai_description": result.get("description"),
                "ai_colors": result.get("colors", []),
                "raw_analysis": result,
            }
        except Exception as e:
            logger.error("asset_processing_failed", error=str(e))
            return {"error": str(e)}
