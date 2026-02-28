import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from src.core.config import settings
import structlog
import json

logger = structlog.get_logger()

class ImageAnalysisService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
            max_tokens=500,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def encode_image(self, image_path: str):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def analyze(self, image_path: str, user_context: str = "") -> dict:
        try:
            base64_image = self.encode_image(image_path)
            
            prompt = """
            Analyze this image for a brand gallery. 
            Provide a JSON output with two keys:
            1. "description": A concise, engaging description suitable for finding this image later for a landing page (e.g., "Diverse team collaborating in a modern office").
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
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ]
            )

            response = await self.llm.ainvoke([message])
            content = response.content
            return json.loads(content)
            
        except Exception as e:
            logger.error("image_analysis_failed", error=str(e))
            return {"description": "Analysis failed", "colors": []}
