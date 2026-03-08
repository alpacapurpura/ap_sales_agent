import logging
import os
from typing import Dict, Any, Optional
import httpx
import urllib.parse
import asyncio
from functools import partial
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.user import User

logger = logging.getLogger(__name__)

class MetaAdapter:
    """
    Adapter for Meta (Facebook) Graph API using facebook_business SDK.
    Handles OAuth2 flow and wraps API operations.
    """
    API_VERSION = "v19.0"
    BASE_URL = "https://graph.facebook.com"
    
    def __init__(self, access_token: Optional[str] = None):
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")
        self.access_token = access_token
        
        if not self.app_id or not self.app_secret:
            logger.warning("META_APP_ID or META_APP_SECRET not set in environment")

        if self.access_token:
            self._init_api()

    def _init_api(self):
        try:
            FacebookAdsApi.init(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=self.access_token,
                api_version=self.API_VERSION
            )
        except Exception as e:
            logger.error(f"Failed to initialize FacebookAdsApi: {e}")
            raise

    def get_authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        """Generates the authorization URL and state."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "state": "meta_auth_state", # TODO: Implement secure state generation
            "response_type": "code",
            "scope": "ads_management,read_insights,pages_show_list,instagram_basic,instagram_manage_comments,instagram_manage_messages,pages_messaging"
        }
        url = f"https://www.facebook.com/{self.API_VERSION}/dialog/oauth?{urllib.parse.urlencode(params)}"
        return url, params["state"]

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchanges the authorization code for an access_token."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "client_secret": self.app_secret,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/{self.API_VERSION}/oauth/access_token",
                params=params
            )
            if response.status_code != 200:
                logger.error(f"Error exchanging code for token: {response.text}")
                response.raise_for_status()
            return response.json()

    async def get_user_profile(self) -> Dict[str, Any]:
        """Gets the user's profile (name, id) using SDK."""
        if not self.access_token:
            raise ValueError("Access token not initialized")
            
        def _get_profile():
            me = User(fbid='me')
            return me.api_get(fields=['id', 'name', 'email'])

        try:
            # Run blocking SDK call in a thread
            profile = await asyncio.to_thread(_get_profile)
            return profile.export_all_data()
        except Exception as e:
            logger.error(f"SDK Error getting user profile: {e}")
            raise
