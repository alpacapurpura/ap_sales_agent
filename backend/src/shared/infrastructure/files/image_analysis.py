"""Image analysis service using vision LLM for brand gallery."""

import base64
import json
from pathlib import Path

import structlog
from langchain_core.messages import HumanMessage
from luana_core_llm.factory import LLMFactory
from luana_core_platform.core.enums import ModelRole

logger = structlog.get_logger()


class ImageAnalysisService:
    """Analyze images for description and dominant colors using vision LLM."""

    def __init__(self) -> None:
        """Initialize with a vision-capable LLM client."""
        base_llm = LLMFactory.get_service().get_client(ModelRole.VISION)
        self.llm = base_llm.bind(
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

    def encode_image(self, image_data: bytes | str) -> str:
        """Accept raw bytes (from cloud storage) or a local file path."""
        if isinstance(image_data, bytes):
            return base64.b64encode(image_data).decode("utf-8")
        with Path(image_data).open("rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze(self, image_data: bytes | str, user_context: str = "") -> dict:
        """Analyze an image and return description and dominant colors."""
        try:
            base64_image = self.encode_image(image_data)

            prompt = """
            Analyze this image for a brand gallery.
            Provide a JSON output with two keys:
            1. "description": A concise, engaging description suitable for finding \
this image later for a landing page (e.g., "Diverse team collaborating in a modern office").
            2. "colors": An array of up to 5 dominant hex color codes found in the image.

            """
            if user_context:
                prompt += f"\nContext provided by user: {user_context}"

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            )

            response = await self.llm.ainvoke([message])
            content = response.content
            return json.loads(content)

        except Exception as e:
            logger.exception("image_analysis_failed", error=str(e))
            return {"description": "Analysis failed", "colors": []}
