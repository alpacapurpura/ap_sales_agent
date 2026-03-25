import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, List

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
)

from src.core.config import settings

# Allow OAuth scope to change
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

logger = logging.getLogger(__name__)

# Scopes for Google Analytics 4 (Read Only)
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly'
]

class GoogleAnalyticsAdapter:
    """
    Adapter for Google Analytics 4 API.
    Handles OAuth2 flow and wraps analytics operations.
    """
    def __init__(self, client_config: Dict[str, str], credentials_data: Optional[Dict[str, Any]] = None):
        self.client_config = client_config
        self.credentials_data = credentials_data
        self.creds = None
        if credentials_data:
            # Ensure client_id and client_secret are in credentials_data for refresh
            if 'client_id' not in credentials_data and client_config.get('client_id'):
                credentials_data['client_id'] = client_config['client_id']
            if 'client_secret' not in credentials_data and client_config.get('client_secret'):
                credentials_data['client_secret'] = client_config['client_secret']
                
            self.creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)

    def get_client_config(self) -> Dict[str, Any]:
        return {
            "web": {
                "client_id": self.client_config.get("client_id"),
                "client_secret": self.client_config.get("client_secret"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def get_authorization_url(self, redirect_uri: str = None) -> tuple[str, str]:
        """Generates the authorization URL and state."""
        flow = Flow.from_client_config(
            self.get_client_config(),
            scopes=SCOPES
        )
        flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url, state

    def exchange_code(self, code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """Exchanges the authorization code for tokens."""
        flow = Flow.from_client_config(
            self.get_client_config(),
            scopes=SCOPES
        )
        
        flow.redirect_uri = redirect_uri or settings.GOOGLE_REDIRECT_URI
        
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            return json.loads(creds.to_json())
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise

    def get_service(self):
        """Returns the Google Analytics Admin service resource."""
        if not self.creds:
            raise ValueError("Credentials not initialized")
        return build('analyticsadmin', 'v1beta', credentials=self.creds)

    def get_account_summaries(self) -> List[Dict[str, Any]]:
        """Gets a list of account summaries which includes accounts and properties."""
        service = self.get_service()
        try:
            # accountSummaries.list returns a structure with account summaries
            response = service.accountSummaries().list().execute()
            return response.get('accountSummaries', [])
        except Exception as e:
            logger.error(f"Error fetching account summaries: {e}")
            raise

    def get_flat_properties(self) -> list[dict[str, str]]:
        """Fetch account summaries and return a flat list of properties.

        Returns:
            [{"property_id": "123", "display_name": "My Site", "account_name": "My Account"}, ...]
        """
        try:
            summaries = self.get_account_summaries()
        except Exception as e:
            logger.warning(f"Could not fetch account summaries: {e}")
            return []

        properties = []
        for account in summaries:
            account_name = account.get("displayName", "")
            for prop in account.get("propertySummaries", []):
                raw_property = prop.get("property", "")
                property_id = raw_property.split("/")[-1] if "/" in raw_property else raw_property
                properties.append({
                    "property_id": property_id,
                    "display_name": prop.get("displayName", property_id),
                    "account_name": account_name,
                })
        return properties

    def _get_data_client(self) -> BetaAnalyticsDataClient:
        """Returns a GA4 Data API client using current credentials."""
        if not self.creds:
            raise ValueError("Credentials not initialized")
        return BetaAnalyticsDataClient(credentials=self.creds)

    async def run_report(
        self,
        property_id: str,
        dimensions: list[str],
        metrics: list[str],
        start_date: str = "30daysAgo",
        end_date: str = "today",
    ) -> dict:
        """
        Run a GA4 report with arbitrary dimensions and metrics.

        Wraps the synchronous BetaAnalyticsDataClient.run_report() call
        in asyncio.to_thread() to avoid blocking the FastAPI event loop.

        Returns a normalized dict:
            {
                "row_count": int,
                "rows": [{"dimensions": [...], "metrics": [...]}, ...],
                "metadata": {"dimensions": [...], "metrics": [...]},
            }
        """
        client = self._get_data_client()
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        )
        response = await asyncio.to_thread(client.run_report, request)
        return self._normalize_report_response(response)

    def _normalize_report_response(self, response) -> dict:
        """Convert GA4 RunReportResponse to a plain dict."""
        rows = []
        for row in response.rows:
            rows.append({
                "dimensions": [dv.value for dv in row.dimension_values],
                "metrics": [mv.value for mv in row.metric_values],
            })
        return {
            "row_count": response.row_count,
            "rows": rows,
            "metadata": {
                "dimensions": [h.name for h in response.dimension_headers],
                "metrics": [h.name for h in response.metric_headers],
            },
        }
