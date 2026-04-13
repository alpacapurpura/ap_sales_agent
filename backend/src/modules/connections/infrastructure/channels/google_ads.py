"""Google Ads API adapter.

Provides an async wrapper around the google-ads Python client for
running GAQL (Google Ads Query Language) queries. The SDK is synchronous,
so all calls are wrapped in asyncio.to_thread() following the same
pattern used for GA4 in google_analytics.py.

Gracefully handles missing developer token by returning empty results.
"""

import asyncio
from datetime import date
from typing import Any

import structlog
from google.auth.exceptions import RefreshError, TransportError

logger = structlog.get_logger(__name__)


class GoogleAdsAdapter:
    """Async adapter for Google Ads reporting via GAQL queries.

    Uses the google-ads Python client wrapped in asyncio.to_thread().
    Returns list of row dicts with campaign fields.
    """

    def __init__(
        self,
        developer_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
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
    ) -> list[dict[str, Any]]:
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
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "google_ads_refresh_token_revoked",
                customer_id=customer_id,
                error=str(exc),
            )
            raise
        except Exception:
            logger.exception("google_ads_query_exception")
            return []

    async def run_search_terms_query(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> list:
        """Execute search_term_view GAQL query for top search terms."""
        query = f"""
            SELECT
                search_term_view.search_term,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros
            FROM search_term_view
            WHERE segments.date BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
                AND campaign.status = 'ENABLED'
            ORDER BY metrics.impressions DESC
            LIMIT 50
        """  # noqa: S608
        if not developer_token:
            return []
        try:
            return await asyncio.to_thread(
                self._run_search_terms_sync,
                customer_id,
                developer_token,
                credentials,
                query,
            )
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "google_ads_search_terms_refresh_revoked",
                customer_id=customer_id,
                error=str(exc),
            )
            raise
        except Exception:
            logger.exception("google_ads_search_terms_exception")
            return []

    def _run_search_terms_sync(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
        query: str,
    ) -> list:
        """Synchronous execution of search_term_view query."""
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
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

        results = []
        try:
            response = ga_service.search(customer_id=customer_id, query=query)
            results.extend(
                {
                    "search_term": row.search_term_view.search_term,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "conversions": row.metrics.conversions,
                    "cost_micros": row.metrics.cost_micros,
                }
                for row in response
            )
        except Exception:
            logger.exception("google_ads_search_terms_search_exception")
        return results

    def _run_query_sync(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
        query: str,
    ) -> list[dict[str, Any]]:
        """Synchronous GAQL query execution using google-ads client.

        Imports google.ads.googleads lazily to avoid import errors when
        the google-ads package is not installed.
        """
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            logger.warning(
                "google_ads_package_not_installed - install google-ads to enable Google Ads provider",
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

        rows: list[dict[str, Any]] = []
        try:
            response = ga_service.search(customer_id=customer_id, query=query)
            rows.extend(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "advertising_channel_type": row.campaign.advertising_channel_type.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "conversions": row.metrics.conversions,
                    "cost_micros": row.metrics.cost_micros,
                    "conversions_value": row.metrics.conversions_value,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc,
                    "segments_date": getattr(
                        getattr(row, "segments", None),
                        "date",
                        "",
                    ),
                }
                for row in response
            )
        except Exception:
            logger.exception("google_ads_search_exception")

        return rows

    async def get_account_currency(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
    ) -> str | None:
        """Query the Google Ads account currency code (ISO 4217).

        Returns the currency_code (e.g. 'USD', 'MXN') or None on failure.
        """
        if not developer_token:
            return None
        try:
            return await asyncio.to_thread(
                self._get_currency_sync,
                customer_id,
                developer_token,
                credentials,
            )
        except Exception:
            logger.exception("google_ads_get_currency_exception")
            return None

    def _get_currency_sync(
        self,
        customer_id: str,
        developer_token: str,
        credentials: dict,
    ) -> str | None:
        """Synchronous query for customer.currency_code."""
        try:
            from google.ads.googleads.client import GoogleAdsClient
        except ImportError:
            return None

        config = {
            "developer_token": developer_token,
            "client_id": credentials.get("client_id", ""),
            "client_secret": credentials.get("client_secret", ""),
            "refresh_token": credentials.get("refresh_token", ""),
            "use_proto_plus": True,
        }
        client = GoogleAdsClient.load_from_dict(config)
        ga_service = client.get_service("GoogleAdsService")

        try:
            query = "SELECT customer.currency_code FROM customer LIMIT 1"
            response = ga_service.search(customer_id=customer_id, query=query)
            for row in response:
                return row.customer.currency_code
        except Exception:
            logger.exception("google_ads_currency_query_exception")
        return None
