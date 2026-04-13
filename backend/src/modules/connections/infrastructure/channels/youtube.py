import json
import logging
import os
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Allow OAuth scope to change
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # noqa: S105

logger = logging.getLogger(__name__)

# Scopes for YouTube: Readonly access to view account info
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


class YoutubeAdapter:
    """
    Adapter for Google YouTube API.
    Handles OAuth2 flow and wraps YouTube operations.
    """

    def __init__(
        self,
        client_config: dict[str, Any],
        credentials_data: dict[str, Any] | None = None,
    ):
        self.client_config = client_config
        self.credentials_data = credentials_data
        self.creds = None

        if credentials_data:
            # Ensure client_id and client_secret are in credentials_data for refresh
            if "client_id" not in credentials_data and client_config.get("client_id"):
                credentials_data["client_id"] = client_config["client_id"]
            if "client_secret" not in credentials_data and client_config.get(
                "client_secret"
            ):
                credentials_data["client_secret"] = client_config["client_secret"]

            self.creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)

    def _get_flow_config(self) -> dict[str, Any]:
        return {
            "web": {
                "client_id": self.client_config.get("client_id"),
                "client_secret": self.client_config.get("client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def get_authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        """Generates the authorization URL and state."""
        flow = Flow.from_client_config(self._get_flow_config(), scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true", prompt="consent"
        )
        return authorization_url, state

    def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchanges the authorization code for tokens."""
        flow = Flow.from_client_config(self._get_flow_config(), scopes=SCOPES)

        flow.redirect_uri = redirect_uri

        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            return json.loads(creds.to_json())
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise

    def get_service(self):
        """Returns the YouTube service resource."""
        if not self.creds:
            msg = "Credentials not initialized"
            raise ValueError(msg)
        return build("youtube", "v3", credentials=self.creds)

    def get_channel_info(self) -> dict[str, Any]:
        """Gets the authenticated user's channel info."""
        service = self.get_service()
        try:
            # Request own channel with snippet and statistics
            response = (
                service.channels()
                .list(mine=True, part="snippet,statistics,contentDetails")
                .execute()
            )

            items = response.get("items", [])
            if not items:
                logger.warning("No YouTube channel found for authenticated user")
                return {}

            channel = items[0]
            return {
                "id": channel.get("id"),
                "title": channel.get("snippet", {}).get("title"),
                "description": channel.get("snippet", {}).get("description"),
                "customUrl": channel.get("snippet", {}).get("customUrl"),
                "thumbnails": channel.get("snippet", {}).get("thumbnails"),
                "statistics": channel.get("statistics"),
                "publishedAt": channel.get("snippet", {}).get("publishedAt"),
            }
        except Exception as e:
            logger.error(f"Error fetching YouTube channel info: {e}")
            raise
