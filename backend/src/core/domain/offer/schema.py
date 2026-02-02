from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Transformation(BaseModel):
    current_situation: str = Field(..., description="Where the client is now (Pain)")
    desired_situation: str = Field(..., description="Where the client wants to be (Heaven)")
    vehicle: str = Field(..., description="The unique mechanism/method name")
    time_to_result: str = Field(..., description="Expected time to see results")

class QualificationCriteria(BaseModel):
    min_budget: Optional[float] = Field(None, description="Minimum required budget")
    required_niche: List[str] = Field(default_factory=list, description="Accepted niches")
    red_flags: List[str] = Field(default_factory=list, description="Criteria for immediate rejection")
    green_flags: List[str] = Field(default_factory=list, description="Criteria for ideal client")

class ProductDetails(BaseModel):
    name: str
    type: Literal["community", "mentorship", "event", "agency", "course"]
    price_full: float
    currency: str = "USD"
    payment_plan: Optional[str] = None
    scarcity_trigger: Optional[str] = None
    deliverables: List[str] = Field(default_factory=list)

class Logistics(BaseModel):
    booking_link: Optional[str] = None
    checkout_link: Optional[str] = None
    guarantee_terms: Optional[str] = None

class ObjectionHandler(BaseModel):
    trigger_keyword: str
    response_script: str

class HighTicketOffer(BaseModel):
    """
    Complete context for a High-Ticket Offer.
    This structure feeds the Sales Agent.
    """
    product_details: ProductDetails
    transformation: Transformation
    qualification: QualificationCriteria
    logistics: Logistics
    objection_handlers: List[ObjectionHandler] = Field(default_factory=list)
    
    # Meta
    anti_avatar: Optional[str] = Field(None, description="Who strictly NOT to sell to")
    social_proof_highlight: Optional[str] = None
