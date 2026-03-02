from typing import Dict, Any, Optional
import structlog
from src.modules.assets.domain.entity import Asset
from src.modules.assets.domain.enums import AssetType

logger = structlog.get_logger()

class AssetProcessor:
    def __init__(self):
        # Initialize services lazily or here
        pass

    async def process_asset(self, asset: Asset, local_path: str) -> Dict[str, Any]:
        """
        Process the asset to extract metadata using AI.
        Currently supports IMAGE analysis via Copilot/OpenAI.
        """
        if asset.type == AssetType.IMAGE:
            return await self._analyze_image(local_path, asset.user_description)
        
        # Future: Video/Audio processing
        return {}

    async def _analyze_image(self, file_path: str, context: Optional[str]) -> Dict[str, Any]:
        try:
            # Dynamically import to avoid circular deps if any, or just standard import
            from src.shared.infrastructure.files.image_analysis import ImageAnalysisService
            
            service = ImageAnalysisService()
            # The service returns specific keys: description, colors
            result = await service.analyze(file_path, user_context=context or "")
            
            return {
                "ai_description": result.get("description"),
                "ai_colors": result.get("colors", []),
                "raw_analysis": result
            }
        except Exception as e:
            logger.error("asset_processing_failed", error=str(e), path=file_path)
            return {"error": str(e)}
