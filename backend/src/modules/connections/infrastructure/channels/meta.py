import asyncio
import secrets
import urllib.parse
from typing import Any

import httpx
import structlog
from facebook_business.adobjects.user import User
from facebook_business.api import FacebookAdsApi
from facebook_business.session import FacebookSession

from src.core.config import settings

logger = structlog.get_logger(__name__)


class MetaAdapter:
    """
    Adapter for Meta (Facebook) Graph API using facebook_business SDK.

    Platform credentials (META_APP_ID / META_APP_SECRET) are read from settings.
    Per-tenant overrides can be provided via constructor params.
    """

    API_VERSION = "v24.0"
    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        access_token: str | None = None,
    ):
        self.app_id = app_id or settings.META_APP_ID
        self.app_secret = app_secret or settings.META_APP_SECRET
        self.access_token = access_token
        self._api_instance = None

        if not self.app_id or not self.app_secret:
            logger.warning("META_APP_ID or META_APP_SECRET not configured")

        if self.access_token:
            self._init_api()

    def _init_api(self):
        """Create a per-instance API object. Never call FacebookAdsApi.init()."""
        try:
            session = FacebookSession(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=self.access_token,
            )
            self._api_instance = FacebookAdsApi(session, api_version=self.API_VERSION)
        except Exception as e:
            logger.error(f"Failed to initialize FacebookAdsApi: {e}")
            raise

    def get_authorization_url(
        self, redirect_uri: str, state: str | None = None
    ) -> tuple[str, str]:
        """Generates the OAuth authorization URL and state token.
        State is always prefixed with 'meta_' so the frontend callback
        can distinguish Meta from Google OAuth redirects."""
        if not state:
            state = f"meta_{secrets.token_urlsafe(32)}"
        elif not state.startswith("meta"):
            state = f"meta_{state}"

        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "response_type": "code",
        }

        # Use Facebook Login for Business config_id if configured (replaces scope)
        if settings.META_CONFIG_ID:
            params["config_id"] = settings.META_CONFIG_ID
            params["override_default_response_type"] = "true"
        else:
            # Fallback to explicit scopes
            params["scope"] = (
                "public_profile,email,pages_show_list,"
                "pages_read_engagement,pages_messaging,"
                "instagram_basic,"
                "instagram_manage_messages,instagram_manage_comments,"
                "ads_read"
            )

        url = f"https://www.facebook.com/{self.API_VERSION}/dialog/oauth?{urllib.parse.urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchanges the authorization code for an access token, then
        automatically extends it to a long-lived token (~60 days)."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "client_secret": self.app_secret,
            "code": code,
        }
        async with httpx.AsyncClient() as client:
            # Step 1: Exchange code for short-lived token
            response = await client.get(
                f"{self.BASE_URL}/{self.API_VERSION}/oauth/access_token",
                params=params,
            )
            if response.status_code != 200:
                logger.error(f"Error exchanging code for token: {response.text}")
                response.raise_for_status()

            token_data = response.json()
            short_lived_token = token_data.get("access_token")

            # Step 2: Exchange short-lived token for long-lived token (~60 days)
            if short_lived_token:
                try:
                    long_lived = await client.get(
                        f"{self.BASE_URL}/{self.API_VERSION}/oauth/access_token",
                        params={
                            "grant_type": "fb_exchange_token",
                            "client_id": self.app_id,
                            "client_secret": self.app_secret,
                            "fb_exchange_token": short_lived_token,
                        },
                    )
                    if long_lived.status_code == 200:
                        long_data = long_lived.json()
                        token_data["access_token"] = long_data.get(
                            "access_token", short_lived_token
                        )
                        token_data["token_type"] = long_data.get("token_type", "bearer")
                        token_data["expires_in"] = long_data.get("expires_in")
                        logger.info("meta_token_extended_to_long_lived")
                    else:
                        logger.warning(f"Could not extend token: {long_lived.text}")
                except Exception as e:
                    logger.warning(f"Token extension failed, using short-lived: {e}")

            return token_data

    async def get_user_profile(self) -> dict[str, Any]:
        """Gets the user's profile (id, name) via the facebook_business SDK."""
        if not self._api_instance:
            raise ValueError("Access token not initialized")

        api = self._api_instance  # Capture for closure — ensures tenant isolation

        def _get_profile():
            me = User(fbid="me", api=api)
            return me.api_get(fields=["id", "name", "email"])

        profile = await asyncio.to_thread(_get_profile)
        return profile.export_all_data()

    async def get_token_permissions(self) -> list[str]:
        """Returns granted permissions for the current access token."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/{self.API_VERSION}/me/permissions",
                params={"access_token": self.access_token},
            )
            if resp.status_code == 200:
                return [
                    p["permission"]
                    for p in resp.json().get("data", [])
                    if p.get("status") == "granted"
                ]
            logger.warning(
                "meta_get_permissions_failed",
                status=resp.status_code,
                body=resp.text[:200],
            )
            return []

    async def get_business_assets(self) -> dict[str, Any]:  # noqa: C901
        """
        Fetches all business assets accessible with the current user/system token:
        - Facebook Pages (with page_access_tokens)
        - Instagram Business Accounts linked to pages
        - Meta Ads Accounts

        Returns a structured dict with keys: pages, instagram_accounts, ads_accounts.
        """
        if not self.access_token:
            raise ValueError("Access token not initialized")

        token = self.access_token
        base = f"{self.BASE_URL}/{self.API_VERSION}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            pages_raw, ads_raw = await asyncio.gather(
                client.get(
                    f"{base}/me/accounts",
                    params={
                        "fields": "id,name,category,picture,fan_count,access_token",
                        "access_token": token,
                    },
                ),
                client.get(
                    f"{base}/me/adaccounts",
                    params={
                        "fields": "id,name,account_id,currency,account_status",
                        "access_token": token,
                    },
                ),
            )

        pages: list[dict[str, Any]] = []
        instagram_accounts: list[dict[str, Any]] = []
        ads_accounts: list[dict[str, Any]] = []

        # ── Facebook Pages ────────────────────────────────────────────────────
        if pages_raw.status_code == 200:
            pages_data = pages_raw.json().get("data", [])

            # Fetch Instagram account linked to each page (parallel)
            async with httpx.AsyncClient(timeout=15.0) as client:
                ig_responses = await asyncio.gather(
                    *[
                        client.get(
                            f"{base}/{page['id']}",
                            params={
                                "fields": "instagram_business_account{id,username,profile_picture_url,followers_count}",
                                "access_token": page.get("access_token", token),
                            },
                        )
                        for page in pages_data
                    ],
                    return_exceptions=True,
                )

            for page, ig_resp in zip(pages_data, ig_responses, strict=False):
                page_entry: dict[str, Any] = {
                    "page_id": page["id"],
                    "page_name": page.get("name", ""),
                    "category": page.get("category"),
                    "picture_url": (
                        page.get("picture", {}).get("data", {}).get("url")
                        if isinstance(page.get("picture"), dict)
                        else None
                    ),
                    "fan_count": page.get("fan_count"),
                    "page_access_token": page.get("access_token"),
                    "instagram_account_id": None,
                    "instagram_username": None,
                }
                pages.append(page_entry)

                # Parse linked Instagram Business account
                # instagram_business_account returns a single object, not an array
                if not isinstance(ig_resp, Exception) and ig_resp.status_code == 200:
                    ig_json = ig_resp.json()
                    logger.info(
                        "meta_ig_raw_response",
                        page_id=page["id"],
                        page_name=page.get("name"),
                        response_keys=list(ig_json.keys()),
                        has_ig=("instagram_business_account" in ig_json),
                    )
                    ig = ig_json.get("instagram_business_account")
                    if ig:
                        page_entry["instagram_account_id"] = ig.get("id")
                        page_entry["instagram_username"] = ig.get("username")
                        instagram_accounts.append(
                            {
                                "ig_account_id": ig.get("id"),
                                "ig_username": ig.get("username", ""),
                                "profile_picture_url": ig.get("profile_picture_url"),
                                "follower_count": ig.get("followers_count"),
                                "linked_page_id": page["id"],
                                "linked_page_name": page.get("name", ""),
                                "page_access_token": page.get("access_token"),
                            }
                        )
                elif isinstance(ig_resp, Exception):
                    logger.warning(
                        "meta_ig_fetch_exception",
                        page_id=page["id"],
                        page_name=page.get("name"),
                        error=str(ig_resp),
                    )
                else:
                    logger.warning(
                        "meta_ig_fetch_failed",
                        page_id=page["id"],
                        page_name=page.get("name"),
                        status=ig_resp.status_code,
                        body=ig_resp.text[:300],
                    )
        else:
            logger.warning(
                "meta_get_pages_failed",
                status=pages_raw.status_code,
                body=pages_raw.text[:200],
            )

        # ── Ad Accounts ───────────────────────────────────────────────────────
        if ads_raw.status_code == 200:
            for ad in ads_raw.json().get("data", []):
                ads_accounts.append(
                    {
                        "ad_account_id": ad.get("account_id")
                        or ad.get("id", "").replace("act_", ""),
                        "ad_account_name": ad.get("name", ""),
                        "currency": ad.get("currency"),
                        "account_status": ad.get("account_status"),
                    }
                )
        else:
            logger.warning(
                "meta_get_adaccounts_failed",
                status=ads_raw.status_code,
                body=ads_raw.text[:200],
            )

        # ── Pixels (per Ad Account) ───────────────────────────────────────────
        pixels: list[dict[str, Any]] = []
        if ads_accounts:
            async with httpx.AsyncClient(timeout=15.0) as client:
                pixel_responses = await asyncio.gather(
                    *[
                        client.get(
                            f"{base}/act_{ad['ad_account_id']}/adspixels",
                            params={"fields": "id,name", "access_token": token},
                        )
                        for ad in ads_accounts
                    ],
                    return_exceptions=True,
                )
            for ad, px_resp in zip(ads_accounts, pixel_responses, strict=False):
                if isinstance(px_resp, Exception):
                    logger.warning(
                        "meta_pixel_fetch_exception",
                        ad_account_id=ad["ad_account_id"],
                        error=str(px_resp),
                    )
                    continue
                if px_resp.status_code != 200:
                    logger.warning(
                        "meta_pixel_fetch_failed",
                        ad_account_id=ad["ad_account_id"],
                        status=px_resp.status_code,
                        body=px_resp.text[:300],
                    )
                    continue
                for px in px_resp.json().get("data", []):
                    pixels.append(
                        {
                            "pixel_id": px.get("id"),
                            "pixel_name": px.get("name", ""),
                            "linked_ad_account_id": ad["ad_account_id"],
                        }
                    )

        # ── WhatsApp Business Accounts (via Business Manager) ─────────────────
        whatsapp_accounts: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                biz_resp = await client.get(
                    f"{base}/me/businesses",
                    params={"fields": "id,name", "access_token": token},
                )
            if biz_resp.status_code == 200:
                businesses = biz_resp.json().get("data", [])
                if businesses:
                    # Fetch WABAs for each business in parallel
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        waba_responses = await asyncio.gather(
                            *[
                                client.get(
                                    f"{base}/{biz['id']}/owned_whatsapp_business_accounts",
                                    params={
                                        "fields": "id,name,currency,timezone_id",
                                        "access_token": token,
                                    },
                                )
                                for biz in businesses
                            ],
                            return_exceptions=True,
                        )

                    wabas: list[dict[str, Any]] = []
                    for biz, waba_resp in zip(businesses, waba_responses, strict=False):
                        if isinstance(waba_resp, Exception):
                            logger.warning(
                                "meta_waba_fetch_exception",
                                business_id=biz["id"],
                                error=str(waba_resp),
                            )
                            continue
                        if waba_resp.status_code != 200:
                            logger.warning(
                                "meta_waba_fetch_failed",
                                business_id=biz["id"],
                                status=waba_resp.status_code,
                                body=waba_resp.text[:300],
                            )
                            continue
                        for waba in waba_resp.json().get("data", []):
                            waba["business_id"] = biz["id"]
                            waba["business_name"] = biz.get("name", "")
                            wabas.append(waba)

                    # Fetch phone numbers for each WABA in parallel
                    if wabas:
                        async with httpx.AsyncClient(timeout=15.0) as client:
                            phone_responses = await asyncio.gather(
                                *[
                                    client.get(
                                        f"{base}/{waba['id']}/phone_numbers",
                                        params={
                                            "fields": "id,display_phone_number,verified_name,quality_rating",
                                            "access_token": token,
                                        },
                                    )
                                    for waba in wabas
                                ],
                                return_exceptions=True,
                            )
                        for waba, ph_resp in zip(wabas, phone_responses, strict=False):
                            phones: list[dict[str, Any]] = []
                            if (
                                not isinstance(ph_resp, Exception)
                                and ph_resp.status_code == 200
                            ):
                                phones = ph_resp.json().get("data", [])
                            elif isinstance(ph_resp, Exception):
                                logger.warning(
                                    "meta_waba_phones_exception",
                                    waba_id=waba["id"],
                                    error=str(ph_resp),
                                )
                            else:
                                logger.warning(
                                    "meta_waba_phones_failed",
                                    waba_id=waba["id"],
                                    status=ph_resp.status_code,
                                    body=ph_resp.text[:300],
                                )

                            whatsapp_accounts.append(
                                {
                                    "waba_id": waba["id"],
                                    "waba_name": waba.get("name", ""),
                                    "currency": waba.get("currency"),
                                    "timezone_id": waba.get("timezone_id"),
                                    "business_id": waba.get("business_id"),
                                    "business_name": waba.get("business_name"),
                                    "phone_numbers": [
                                        {
                                            "phone_number_id": ph.get("id"),
                                            "display_phone_number": ph.get(
                                                "display_phone_number"
                                            ),
                                            "verified_name": ph.get("verified_name"),
                                            "quality_rating": ph.get("quality_rating"),
                                        }
                                        for ph in phones
                                    ],
                                }
                            )
            else:
                logger.warning(
                    "meta_get_businesses_failed",
                    status=biz_resp.status_code,
                    body=biz_resp.text[:200],
                )
        except Exception as e:
            logger.warning("meta_whatsapp_fetch_error", error=str(e))

        return {
            "pages": pages,
            "instagram_accounts": instagram_accounts,
            "ads_accounts": ads_accounts,
            "pixels": pixels,
            "whatsapp_accounts": whatsapp_accounts,
        }
