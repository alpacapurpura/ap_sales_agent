import logging
import secrets
from typing import Dict, Any, Optional, List
import httpx
import urllib.parse
import asyncio
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.user import User

from src.core.config import settings

logger = logging.getLogger(__name__)


class MetaAdapter:
    """
    Adapter for Meta (Facebook) Graph API using facebook_business SDK.

    Platform credentials (META_APP_ID / META_APP_SECRET) are read from settings.
    Per-tenant overrides can be provided via constructor params.
    """

    API_VERSION = "v19.0"
    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        self.app_id = app_id or settings.META_APP_ID
        self.app_secret = app_secret or settings.META_APP_SECRET
        self.access_token = access_token

        if not self.app_id or not self.app_secret:
            logger.warning("META_APP_ID or META_APP_SECRET not configured")

        if self.access_token:
            self._init_api()

    def _init_api(self):
        try:
            FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=self.access_token,
                api_version=self.API_VERSION,
            )
        except Exception as e:
            logger.error(f"Failed to initialize FacebookAdsApi: {e}")
            raise

    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> tuple[str, str]:
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
                "instagram_manage_messages,instagram_manage_comments,"
                "ads_read"
            )

        url = f"https://www.facebook.com/{self.API_VERSION}/dialog/oauth?{urllib.parse.urlencode(params)}"
        return url, state

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
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
                        token_data["access_token"] = long_data.get("access_token", short_lived_token)
                        token_data["token_type"] = long_data.get("token_type", "bearer")
                        token_data["expires_in"] = long_data.get("expires_in")
                        logger.info("meta_token_extended_to_long_lived")
                    else:
                        logger.warning(f"Could not extend token: {long_lived.text}")
                except Exception as e:
                    logger.warning(f"Token extension failed, using short-lived: {e}")

            return token_data

    async def get_user_profile(self) -> Dict[str, Any]:
        """Gets the user's profile (id, name) via the facebook_business SDK."""
        if not self.access_token:
            raise ValueError("Access token not initialized")

        def _get_profile():
            me = User(fbid="me")
            return me.api_get(fields=["id", "name", "email"])

        profile = await asyncio.to_thread(_get_profile)
        return profile.export_all_data()

    async def get_business_assets(self) -> Dict[str, Any]:
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

        pages: List[Dict[str, Any]] = []
        instagram_accounts: List[Dict[str, Any]] = []
        ads_accounts: List[Dict[str, Any]] = []

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
                                "fields": "instagram_accounts{id,username,profile_picture_url,followers_count}",
                                "access_token": page.get("access_token", token),
                            },
                        )
                        for page in pages_data
                    ],
                    return_exceptions=True,
                )

            for page, ig_resp in zip(pages_data, ig_responses):
                page_entry: Dict[str, Any] = {
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

                # Parse linked Instagram account
                if not isinstance(ig_resp, Exception) and ig_resp.status_code == 200:
                    ig_data = ig_resp.json().get("instagram_accounts", {}).get("data", [])
                    if ig_data:
                        ig = ig_data[0]
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
                        "ad_account_id": ad.get("account_id") or ad.get("id", "").replace("act_", ""),
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

        return {
            "pages": pages,
            "instagram_accounts": instagram_accounts,
            "ads_accounts": ads_accounts,
        }
