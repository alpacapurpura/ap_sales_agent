from typing import TypedDict, Optional, Dict, Any, List

class WebExtractorState(TypedDict):
    """
    State for the Web Extractor Subgraph.
    """
    # Navigation State
    base_url: str             # The starting URL
    current_url: str          # Current URL being processed
    queue: List[str]          # URLs to visit
    visited: List[str]        # Visited URLs
    depth: int                # Current depth
    max_depth: int            # Max depth limit
    mode: Optional[str]       # Mode: 'crawl_only' or 'extract'
    
    # Data State
    target_schema: Dict[str, Any]  # JSON Schema derived from Pydantic model
    prompt_template: Optional[str] # Specific prompt for the extraction task
    aggregated_content: List[str]  # Content collected from all pages
    
    # Legacy/Result State
    raw_content: Optional[str]     # Content of current page (temporary)
    extracted_data: Optional[Dict[str, Any]] # Final structured data
    error: Optional[str]
    retry_count: int
