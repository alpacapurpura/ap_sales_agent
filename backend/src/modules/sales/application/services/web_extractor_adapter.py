from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from src.modules.sales.application.agents.web_extractor.graph import web_extractor_graph

T = TypeVar("T", bound=BaseModel)

async def extract_from_url(
    url: str, 
    schema: Type[T], 
    max_depth: int = 0,
    prompt_template: Optional[str] = None
) -> Optional[T]:
    """
    Extracts structured data from a URL using the Web Extractor Subgraph.
    Supports Deep Crawling via max_depth.
    
    Args:
        url: The URL to scrape.
        schema: The Pydantic model class defining the expected data structure.
        max_depth: How many levels deep to crawl (0 = only url, 1 = follow links from url).
        prompt_template: Optional system prompt override.
        
    Returns:
        An instance of the Pydantic model populated with extracted data, or None if failed.
    """
    # Convert Pydantic model to JSON Schema for the LLM
    json_schema = schema.model_json_schema()
    
    # Initialize state
    initial_state = {
        # Navigation
        "base_url": url,
        "current_url": None, # Will be set by scheduler
        "queue": [url],      # Start with base url
        "visited": [],
        "depth": 0,
        "max_depth": max_depth,
        
        # Data
        "target_schema": json_schema,
        "prompt_template": prompt_template,
        "aggregated_content": [],
        
        # Legacy/Result
        "retry_count": 0,
        "error": None,
        "raw_content": None,
        "extracted_data": None
    }
    
    # Invoke the graph
    try:
        result = await web_extractor_graph.ainvoke(initial_state)
        
        if result.get("error"):
            print(f"Web Extraction Error for {url}: {result['error']}")
            return None
            
        extracted_data = result.get("extracted_data")
        if not extracted_data:
            return None
            
        # Validate and return Pydantic model
        return schema.model_validate(extracted_data)
        
    except Exception as e:
        print(f"Web Extraction Critical Error: {e}")
        return None
