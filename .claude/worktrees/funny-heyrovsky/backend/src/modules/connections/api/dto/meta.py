from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class MetaConfigRequest(BaseModel):
    app_id: str
    app_secret: str


class MetaStatusResponse(BaseModel):
    is_connected: bool
    is_configured: bool = False
    name: Optional[str] = None
    account_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


# ── Asset DTOs ────────────────────────────────────────────────────────────────

class FacebookPageAsset(BaseModel):
    page_id: str
    page_name: str
    category: Optional[str] = None
    picture_url: Optional[str] = None
    fan_count: Optional[int] = None
    instagram_account_id: Optional[str] = None
    instagram_username: Optional[str] = None
    is_active: bool = False
    has_credentials: bool = False


class InstagramAccountAsset(BaseModel):
    ig_account_id: str
    ig_username: str
    profile_picture_url: Optional[str] = None
    follower_count: Optional[int] = None
    linked_page_id: Optional[str] = None
    linked_page_name: Optional[str] = None
    is_active: bool = False
    has_credentials: bool = False


class MetaAdsAccountAsset(BaseModel):
    ad_account_id: str
    ad_account_name: str
    currency: Optional[str] = None
    account_status: Optional[int] = None  # 1=ACTIVE, 2=DISABLED, 3=UNSETTLED...
    is_active: bool = False
    has_credentials: bool = False


class MetaAssetsResponse(BaseModel):
    pages: List[FacebookPageAsset] = []
    instagram_accounts: List[InstagramAccountAsset] = []
    ads_accounts: List[MetaAdsAccountAsset] = []


class ToggleAssetRequest(BaseModel):
    is_active: bool
