"""TikTok Business API adapter.

Provides async methods for fetching organic insights and ads reports
from TikTok's Business API v1.3.

NOTE: TikTok access tokens expire after 24 hours, much faster than
Meta (~60 days) or Google (1 hour with refresh). The ConnectionPortImpl
needs TikTok-specific refresh logic. This adapter handles graceful
degradation when tokens are expired or missing.
"""

import logging
from datetime import date
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

TIKTOK_API_BASE = "https://business-api.tiktok.com/open_api/v1.3"


class TikTokAdapter:
    """Async adapter for TikTok Business API.

    Uses httpx async client with 30s timeout against TikTok's REST API.
    All methods return empty lists on failure (graceful degradation).
    """

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    async def get_organic_insights(
        self,
        access_token: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch organic video insights (video_views, likes, comments, shares).

        Returns a list of dicts with metric data, or empty list on failure.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{TIKTOK_API_BASE}/business/get/",
                    headers={"Access-Token": access_token},
                    params={
                        "business_id": "",  # Will be set per tenant
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "fields": '["video_views","likes","comments","shares"]',
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        "tiktok_organic_insights_failed status=%d body=%s",
                        response.status_code,
                        response.text[:200],
                    )
                    return []
                data = response.json()
                if data.get("code") != 0:
                    logger.warning(
                        "tiktok_organic_insights_error code=%s message=%s",
                        data.get("code"),
                        data.get("message", ""),
                    )
                    return []
                return data.get("data", {}).get("metrics", [])
        except Exception:
            logger.exception("tiktok_organic_insights_exception")
            return []

    async def get_ads_report(
        self,
        access_token: str,
        advertiser_id: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """Fetch TikTok Ads campaign-level report.

        Returns a list of row dicts with reach, clicks, conversions, spend,
        or empty list on failure.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{TIKTOK_API_BASE}/report/integrated/get/",
                    headers={"Access-Token": access_token},
                    params={
                        "advertiser_id": advertiser_id,
                        "report_type": "BASIC",
                        "data_level": "AUCTION_ADVERTISER",
                        "dimensions": '["stat_time_day"]',
                        "metrics": '["reach","clicks","conversion","spend"]',
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        "tiktok_ads_report_failed status=%d body=%s",
                        response.status_code,
                        response.text[:200],
                    )
                    return []
                data = response.json()
                if data.get("code") != 0:
                    logger.warning(
                        "tiktok_ads_report_error code=%s message=%s",
                        data.get("code"),
                        data.get("message", ""),
                    )
                    return []
                return data.get("data", {}).get("list", [])
        except Exception:
            logger.exception("tiktok_ads_report_exception")
            return []
