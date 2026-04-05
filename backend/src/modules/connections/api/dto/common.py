"""Shared response DTOs for the connections module."""

from typing import Any

from pydantic import BaseModel


class ConnectionTestResponse(BaseModel):
    """Generic response for test_connection endpoints."""

    status: str
    message: str
    data: dict[str, Any] | None = None


class StatusSavedResponse(BaseModel):
    """Generic response for config-save / save operations."""

    status: str


class BookingLinkResponse(BaseModel):
    """Response for booking link creation endpoints."""

    token: str
    url: str


class PersonalizedLinkResponse(BaseModel):
    """Response for personalized booking link creation."""

    token: str
    url: str
    expires_at: Any  # datetime — Any for JSON serialisation compatibility


class BookMeetingResponse(BaseModel):
    """Response for book_meeting endpoint."""

    status: str
    event_link: str | None = None


class AppointmentItem(BaseModel):
    """Single appointment item."""

    id: str | None = None
    summary: str | None = None
    start: str | None = None
    end: str | None = None
    meet_link: str | None = None
    attendees: list[str] = []


class SlotsResponse(BaseModel):
    """Response for get_slots endpoint."""

    slots: list[Any]


class WorkspaceServiceStatus(BaseModel):
    """Per-service status for the Google Workspace status endpoint."""

    is_active: bool
    has_credentials: bool


class WorkspaceStatusResponse(BaseModel):
    """Response for Google Workspace get_status endpoint."""

    is_connected: bool
    email: str | None = None
    services: dict[str, WorkspaceServiceStatus]


class ToggleServiceResponse(BaseModel):
    """Response for toggle_service endpoint."""

    status: str
    service: str
    is_active: bool


class SetPrimaryAssetResponse(BaseModel):
    """Response for set_primary_asset endpoint."""

    status: str
    asset_type: str
    asset_id: str


class ToggleAssetResponse(BaseModel):
    """Response for toggle_asset endpoint."""

    status: str
    channel_type: str
    asset_id: str
    is_active: bool


class TelegramConnectResponse(BaseModel):
    """Response for connect_telegram endpoint."""

    status: str
    bot: dict[str, Any]


class WhatsAppStatusItem(BaseModel):
    """Status for a single WhatsApp provider."""

    status: str
    profile: dict[str, Any] | None = None


class WhatsAppStatusResponse(BaseModel):
    """Response for get_whatsapp_status endpoint."""

    evolution: WhatsAppStatusItem
    meta: WhatsAppStatusItem


class WhatsAppSessionResponse(BaseModel):
    """Response for create_whatsapp_session endpoint."""

    status: str
    instance: str | None = None
    message: str | None = None


class WhatsAppQRResponse(BaseModel):
    """Response for get_whatsapp_qr endpoint."""

    code: str | None = None


class YouTubeAnalyticsStatusResponse(BaseModel):
    """Response for youtube_analytics get_status endpoint."""

    is_connected: bool
    channel_id: str | None = None


class YouTubeAnalyticsDataResponse(BaseModel):
    """Generic response for YouTube Analytics data endpoints (overview, daily-views, etc.)."""

    status: str
    data: Any
    start_date: str
    end_date: str


class YoutubeUpdateConfigResponse(BaseModel):
    """Response for youtube update_config endpoint."""

    status: str
    message: str
