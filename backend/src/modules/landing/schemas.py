from typing import Any

from pydantic import BaseModel


class RegenerateBlockRequest(BaseModel):
    current_content: str
    block_type: str
    context: dict[str, Any] | None = None
