from pydantic import BaseModel


class GA4PropertySummary(BaseModel):
    property_id: str
    display_name: str
    account_name: str = ""


class PropertySelectRequest(BaseModel):
    property_id: str


class SelectedProperty(BaseModel):
    property_id: str
    display_name: str


class GoogleAnalyticsStatusResponse(BaseModel):
    is_connected: bool
    is_configured: bool = False
    selected_property: SelectedProperty | None = None


class GoogleAnalyticsCallbackResponse(BaseModel):
    status: str
    properties: list[GA4PropertySummary] = []


class PropertySelectResponse(BaseModel):
    status: str
    property_id: str
    display_name: str
