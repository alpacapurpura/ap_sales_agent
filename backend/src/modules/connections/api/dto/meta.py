"""Meta DTOs."""

from typing import Any

from pydantic import BaseModel


class MetaConfigRequest(BaseModel):
    """Meta Config Request DTO."""

    app_id: str
    app_secret: str


class MetaStatusResponse(BaseModel):
    """Meta Status Response DTO."""

    is_connected: bool
    is_configured: bool = False
    name: str | None = None
    account_id: str | None = None
    config: dict[str, Any] | None = None


# ── Asset DTOs ────────────────────────────────────────────────────────────────


class FacebookPageAsset(BaseModel):
    """Facebook Page Asset DTO."""

    page_id: str
    page_name: str
    category: str | None = None
    picture_url: str | None = None
    fan_count: int | None = None
    instagram_account_id: str | None = None
    instagram_username: str | None = None
    is_active: bool = False
    has_credentials: bool = False


class InstagramAccountAsset(BaseModel):
    """Instagram Account Asset DTO."""

    ig_account_id: str
    ig_username: str
    profile_picture_url: str | None = None
    follower_count: int | None = None
    linked_page_id: str | None = None
    linked_page_name: str | None = None
    is_active: bool = False
    has_credentials: bool = False


class MetaAdsAccountAsset(BaseModel):
    """Meta Ads Account Asset DTO."""

    ad_account_id: str
    ad_account_name: str
    currency: str | None = None
    account_status: int | None = None  # 1=ACTIVE, 2=DISABLED, 3=UNSETTLED...
    is_active: bool = False
    has_credentials: bool = False


class MetaPixelAsset(BaseModel):
    """Meta Pixel Asset DTO."""

    pixel_id: str
    pixel_name: str
    linked_ad_account_id: str | None = None
    is_active: bool = False
    has_credentials: bool = False


class WhatsAppPhoneNumber(BaseModel):
    """Whats App Phone Number DTO."""

    phone_number_id: str
    display_phone_number: str | None = None
    verified_name: str | None = None
    quality_rating: str | None = None


class WhatsAppBusinessAsset(BaseModel):
    """Whats App Business Asset DTO."""

    waba_id: str
    waba_name: str
    currency: str | None = None
    timezone_id: str | None = None
    business_id: str | None = None
    business_name: str | None = None
    phone_numbers: list[WhatsAppPhoneNumber] = []
    is_active: bool = False
    has_credentials: bool = False


class MetaAssetsResponse(BaseModel):
    """Meta Assets Response DTO."""

    pages: list[FacebookPageAsset] = []
    instagram_accounts: list[InstagramAccountAsset] = []
    ads_accounts: list[MetaAdsAccountAsset] = []
    pixels: list[MetaPixelAsset] = []
    whatsapp_accounts: list[WhatsAppBusinessAsset] = []
    warnings: list[str] | None = None


class ToggleAssetRequest(BaseModel):
    """Toggle Asset Request DTO."""

    is_active: bool
