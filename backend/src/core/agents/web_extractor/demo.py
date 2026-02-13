import asyncio
from pydantic import BaseModel, Field
from typing import List, Optional
from src.core.services.web_extractor_adapter import extract_from_url

# --- Schema 1: Company Data (For Onboarding/Sales) ---
class CompanyData(BaseModel):
    name: str = Field(..., description="Name of the company")
    industry: str = Field(..., description="Industry or sector")
    value_proposition: str = Field(..., description="Main value proposition or slogan")
    key_products: List[str] = Field(default_factory=list, description="List of key products or services")

# --- Schema 2: Lead Data (For Lead Qualification) ---
class LeadData(BaseModel):
    full_name: str = Field(..., description="Full name of the person")
    job_title: str = Field(..., description="Job title or role")
    email: Optional[str] = Field(None, description="Email address if found")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    
# --- Schema 3: News Data (For Research) ---
class NewsArticle(BaseModel):
    headline: str = Field(..., description="Main headline")
    summary: str = Field(..., description="Brief summary of the article")
    publication_date: Optional[str] = Field(None, description="Date of publication")

async def run_demo():
    """
    Demonstrates how the SAME extractor graph handles completely different data types
    just by passing a different Pydantic schema.
    """
    
    # Example 1: Extract Company Info
    # This simulates what the 'Researcher' node in Onboarding would do
    url_company = "https://openai.com/about" 
    print(f"--- Extracting Company Data from {url_company} ---")
    company_info = await extract_from_url(url_company, CompanyData)
    
    if company_info:
        print(f"Found Company: {company_info.name}")
        print(f"Industry: {company_info.industry}")
        print(f"Value Prop: {company_info.value_proposition}")
    else:
        print("Failed to extract company info.")
    
    # Example 2: Extract Lead Info
    # This simulates what a 'LeadEnricher' node would do
    url_profile = "https://www.linkedin.com/in/satyanadella/" # (Note: scraping LinkedIn is hard, this is just example)
    print(f"\n--- Extracting Lead Data from {url_profile} ---")
    lead_info = await extract_from_url(url_profile, LeadData)
    
    if lead_info:
        print(f"Found Person: {lead_info.full_name}")
        print(f"Role: {lead_info.job_title}")
    else:
        print("Failed to extract lead info (likely 403 or empty).")

if __name__ == "__main__":
    asyncio.run(run_demo())
