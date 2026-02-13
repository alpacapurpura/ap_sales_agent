from typing import TypedDict, Optional, Dict, Any

class WebExtractorState(TypedDict):
    """
    State for the Web Extractor Subgraph.
    """
    url: str
    target_schema: Dict[str, Any]  # JSON Schema derived from Pydantic model
    raw_content: Optional[str]     # Cleaned HTML content
    extracted_data: Optional[Dict[str, Any]] # Final structured data
    error: Optional[str]
    retry_count: int
