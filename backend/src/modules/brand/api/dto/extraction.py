from typing import Literal

from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field(
        "brand_identity", description="Type of extraction to perform"
    )
