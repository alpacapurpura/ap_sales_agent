import os
from typing import List, Dict, Any
from langchain_community.tools.tavily_search import TavilySearchResults

class ResearchService:
    """
    Service for web research using Tavily (or fallback).
    """
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        if self.api_key:
            self.tool = TavilySearchResults(max_results=3)
        else:
            self.tool = None
            
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a web search.
        """
        if not self.tool:
            print("Warning: TAVILY_API_KEY not found. Returning mock results.")
            return [{"url": "http://mock.com", "content": f"Mock content for {query}"}]
            
        try:
            results = self.tool.invoke({"query": query})
            return results
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def analyze_url(self, url: str) -> str:
        """
        Deep analysis of a specific URL (scraping).
        Placeholder for now.
        """
        # Here we would use a scraper like Firecrawl or simple requests+BeautifulSoup
        return f"Content scraped from {url} (Placeholder)"

# Singleton
research_service = ResearchService()
