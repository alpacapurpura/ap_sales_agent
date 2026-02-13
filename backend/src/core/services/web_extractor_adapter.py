from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from src.core.agents.web_extractor.graph import web_extractor_graph

T = TypeVar("T", bound=BaseModel)

async def extract_from_url(url: str, schema: Type[T]) -> Optional[T]:
    """
    Extracts structured data from a URL using the Web Extractor Subgraph.
    
    Args:
        url: The URL to scrape.
        schema: The Pydantic model class defining the expected data structure.
        
    Returns:
        An instance of the Pydantic model populated with extracted data, or None if failed.
    """
    # Convert Pydantic model to JSON Schema for the LLM
    json_schema = schema.model_json_schema()
    
    # Initialize state
    initial_state = {
        "url": url,
        "target_schema": json_schema,
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
