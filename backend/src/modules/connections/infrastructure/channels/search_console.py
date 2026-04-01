"""Google Search Console API adapter.

Provides analytics from Google Search Console's searchanalytics.query endpoint.
Uses the same Google OAuth credentials as google_analytics (workspace flow).
"""
import asyncio
import logging
from datetime import date
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


class SearchConsoleAdapter:
    """Adapter for Google Search Console API (searchanalytics).

    Uses the same OAuth credentials stored in ChannelConnection.credentials
    from the Google Workspace OAuth flow.
    """

    def __init__(self, credentials_data: Dict[str, Any]):
        self.creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)

    def _get_service(self):
        return build("searchconsole", "v1", credentials=self.creds)

    async def query_analytics(
        self,
        site_url: str,
        start_date: date,
        end_date: date,
        dimensions: Optional[List[str]] = None,
        row_limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Query Search Console analytics data."""
        return await asyncio.to_thread(
            self._query_sync, site_url, start_date, end_date, dimensions, row_limit
        )

    def _query_sync(
        self,
        site_url: str,
        start_date: date,
        end_date: date,
        dimensions: Optional[List[str]],
        row_limit: int,
    ) -> List[Dict[str, Any]]:
        try:
            service = self._get_service()
            body: Dict[str, Any] = {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "rowLimit": row_limit,
            }
            if dimensions:
                body["dimensions"] = dimensions
            response = (
                service.searchanalytics()
                .query(siteUrl=site_url, body=body)
                .execute()
            )
            return response.get("rows", [])
        except Exception:
            logger.exception("search_console_query_failed site=%s", site_url)
            return []

    async def list_sites(self) -> List[Dict[str, Any]]:
        """List verified sites for the authenticated user."""
        return await asyncio.to_thread(self._list_sites_sync)

    def _list_sites_sync(self) -> List[Dict[str, Any]]:
        try:
            service = self._get_service()
            response = service.sites().list().execute()
            return response.get("siteEntry", [])
        except Exception:
            logger.exception("search_console_list_sites_failed")
            return []
