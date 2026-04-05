from typing import Any

from pydantic import BaseModel


class MetaConfigRequest(BaseModel):
    app_id: str
    app_secret: str


class MetaStatusResponse(BaseModel):
    is_connected: bool
    is_configured: bool = False
    name: str | None = None
    account_id: str | None = None
    config: dict[str, Any] | None = None


# ── Asset DTOs ────────────────────────────────────────────────────────────────


class FacebookPageAsset(BaseModel):
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
    ig_account_id: str
    ig_username: str
    profile_picture_url: str | None = None
    follower_count: int | None = None
    linked_page_id: str | None = None
    linked_page_name: str | None = None
    is_active: bool = False
    has_credentials: bool = False


class MetaAdsAccountAsset(BaseModel):
    ad_account_id: str
    ad_account_name: str
    currency: str | None = None
    account_status: int | None = None  # 1=ACTIVE, 2=DISABLED, 3=UNSETTLED...
    is_active: bool = False
    has_credentials: bool = False


class MetaPixelAsset(BaseModel):
    pixel_id: str
    pixel_name: str
    linked_ad_account_id: str | None = None
    is_active: bool = False
    has_credentials: bool = False


class WhatsAppPhoneNumber(BaseModel):
    phone_number_id: str
    display_phone_number: str | None = None
    verified_name: str | None = None
    quality_rating: str | None = None


class WhatsAppBusinessAsset(BaseModel):
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
    pages: list[FacebookPageAsset] = []
    instagram_accounts: list[InstagramAccountAsset] = []
    ads_accounts: list[MetaAdsAccountAsset] = []
    pixels: list[MetaPixelAsset] = []
    whatsapp_accounts: list[WhatsAppBusinessAsset] = []
    warnings: list[str] | None = None


class ToggleAssetRequest(BaseModel):
    is_active: bool
