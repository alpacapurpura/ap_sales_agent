from pydantic import BaseModel, Field
from typing import Literal

class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field("brand_identity", description="Type of extraction to perform")
