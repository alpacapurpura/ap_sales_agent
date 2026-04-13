"""Google Analytics DTOs."""

from pydantic import BaseModel


class GA4PropertySummary(BaseModel):
    """GA4Property Summary DTO."""

    property_id: str
    display_name: str
    account_name: str = ""


class PropertySelectRequest(BaseModel):
    """Property Select Request DTO."""

    property_id: str


class SelectedProperty(BaseModel):
    """Selected Property DTO."""

    property_id: str
    display_name: str


class GoogleAnalyticsStatusResponse(BaseModel):
    """Google Analytics Status Response DTO."""

    is_connected: bool
    is_configured: bool = False
    selected_property: SelectedProperty | None = None


class GoogleAnalyticsCallbackResponse(BaseModel):
    """Google Analytics Callback Response DTO."""

    status: str
    properties: list[GA4PropertySummary] = []


class PropertySelectResponse(BaseModel):
    """Property Select Response DTO."""

    status: str
    property_id: str
    display_name: str
