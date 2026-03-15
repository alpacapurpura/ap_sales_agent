"""Google Ads API adapter.

Provides an async wrapper around the google-ads Python client for
running GAQL (Google Ads Query Language) queries. The SDK is synchronous,
so all calls are wrapped in asyncio.to_thread() following the same
pattern used for GA4 in google_analytics.py.

Gracefully handles missing developer token by returning empty results.
"""

import asyncio
import logging
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GoogleAdsAdapter:
    """Async adapter for Google Ads reporting via GAQL queries.

    Uses the google-ads Python client wrapped in asyncio.to_thread().
    Returns list of row dicts with campaign fields.
    """

    def __init__(
        self,
        developer_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        self.developer_token = developer_token
        self.client_id = client_id
        self.client_secret = client_secret

    async def run_gaql_query(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
        query: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Run a GAQL query against the Google Ads API.

        Args:
            customer_id: Google Ads customer ID (without dashes).
            developer_token: Google Ads API developer token.
            credentials: OAuth credentials dict with access_token, refresh_token, etc.
            query: GAQL query string with {start} and {end} placeholders.
            start_date: Query start date.
            end_date: Query end date.

        Returns:
            List of row dicts with campaign and metric fields.
            Returns empty list on any error (graceful degradation).
        """
        if not developer_token:
            logger.warning("google_ads_missing_developer_token")
            return []

        formatted_query = query.format(
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

        try:
            return await asyncio.to_thread(
                self._run_query_sync,
                customer_id,
                developer_token,
                credentials,
                formatted_query,
            )
        except Exception:
            logger.exception("google_ads_query_exception")
            return []

    def _run_query_sync(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Synchronous GAQL query execution using google-ads client.

        Imports google.ads.googleads lazily to avoid import errors when
        the google-ads package is not installed.
        """
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            logger.warning(
                "google_ads_package_not_installed - install google-ads to enable Google Ads provider"
            )
            return []

        config = {
            "developer_token": developer_token,
            "client_id": credentials.get("client_id", ""),
            "client_secret": credentials.get("client_secret", ""),
            "refresh_token": credentials.get("refresh_token", ""),
            "use_proto_plus": True,
        }
        client = GoogleAdsClient.load_from_dict(config)
        ga_service = client.get_service("GoogleAdsService")

        rows: List[Dict[str, Any]] = []
        try:
            response = ga_service.search(
                customer_id=customer_id, query=query
            )
            for row in response:
                rows.append(
                    {
                        "campaign_id": str(row.campaign.id),
                        "campaign_name": row.campaign.name,
                        "advertising_channel_type": row.campaign.advertising_channel_type.name,
                        "impressions": row.metrics.impressions,
                        "clicks": row.metrics.clicks,
                        "conversions": row.metrics.conversions,
                        "cost_micros": row.metrics.cost_micros,
                    }
                )
        except Exception:
            logger.exception("google_ads_search_exception")

        return rows
