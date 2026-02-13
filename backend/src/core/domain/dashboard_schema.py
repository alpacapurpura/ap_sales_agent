from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class DashboardMetrics(BaseModel):
    """
    Key Performance Indicators for the dashboard.
    Resilient to extra fields.
    """
    model_config = ConfigDict(extra='ignore')
    
    pipeline_value: float = Field(..., description="Estimated total value of leads in pipeline")
    active_leads_count: int = Field(..., description="Number of leads currently engaged")
    conversion_rate: float = Field(..., description="Percentage of leads converted to bookings")
    # Future proofing: extra fields won't break the model

class ActionItem(BaseModel):
    """
    Represents a task requiring human attention.
    Abstracts the source (Telegram, WhatsApp, System Error) into a generic item.
    """
    model_config = ConfigDict(extra='ignore')
    
    id: str = Field(..., description="Unique ID of the item")
    type: str = Field(..., description="Type of action: INTERVENTION, GAP, BOOKING, ALERT")
    priority: str = Field(..., description="HIGH, MEDIUM, LOW")
    title: str = Field(..., description="Short title")
    description: str = Field(..., description="Detailed description")
    link: Optional[str] = Field(None, description="Link to resolve the action (e.g., /audit?lead_id=123)")
    timestamp: str = Field(..., description="ISO timestamp")

class AgendaItem(BaseModel):
    """
    Represents a scheduled event.
    """
    model_config = ConfigDict(extra='ignore')
    
    id: str
    title: str
    start_time: str
    attendee_name: str
    status: str

class FunnelStage(BaseModel):
    """
    Data point for the funnel chart.
    """
    stage: str
    count: int
    value: float = 0.0

class DashboardResponse(BaseModel):
    """
    Main response object for /api/v1/dashboard/summary
    """
    model_config = ConfigDict(extra='ignore')
    
    metrics: DashboardMetrics
    action_items: List[ActionItem]
    agenda: List[AgendaItem]
    funnel: List[FunnelStage]
