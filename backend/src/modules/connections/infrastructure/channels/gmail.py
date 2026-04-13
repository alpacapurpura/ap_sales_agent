import base64
import json
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from src.core.config import settings

# Allow OAuth scope to change
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # noqa: S105

logger = logging.getLogger(__name__)

# Scopes for Gmail: Send emails and read profile (to get email address)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


class GmailAdapter:
    """
    Adapter for Google Gmail API.
    Handles OAuth2 flow and wraps email operations.
    """

    def __init__(self, credentials_data: dict[str, Any] | None = None):
        self.credentials_data = credentials_data
        self.creds = None
        if credentials_data:
            self.creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)

    @staticmethod
    def get_client_config() -> dict[str, Any]:
        return {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
        }

    @staticmethod
    def get_authorization_url(redirect_uri: str = None) -> tuple[str, str]:
        """Generates the authorization URL and state."""
        flow = Flow.from_client_config(GmailAdapter.get_client_config(), scopes=SCOPES)
        flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url, state

    @staticmethod
    def exchange_code(code: str, redirect_uri: str = None) -> dict[str, Any]:
        """Exchanges the authorization code for tokens."""
        flow = Flow.from_client_config(GmailAdapter.get_client_config(), scopes=SCOPES)

        flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI

        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            return json.loads(creds.to_json())
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise

    def get_service(self):
        """Returns the Gmail service resource."""
        if not self.creds:
            msg = "Credentials not initialized"
            raise ValueError(msg)
        return build("gmail", "v1", credentials=self.creds)

    def get_profile(self) -> dict[str, Any]:
        """Gets the user's profile (email address)."""
        service = self.get_service()
        try:
            profile = service.users().getProfile(userId="me").execute()
            if not profile or "emailAddress" not in profile:
                logger.error(f"Gmail Profile Response Invalid: {profile}")
                msg = "Could not retrieve email address from Gmail API"
                raise ValueError(msg)
            return profile
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            raise

    def send_email(self, to_email: str, subject: str, body_html: str) -> dict[str, Any]:
        """Sends an HTML email."""
        service = self.get_service()

        message = MIMEMultipart()
        message["to"] = to_email
        message["subject"] = subject
        message.attach(MIMEText(body_html, "html"))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        try:
            message = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )
            return message
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            raise
