"""
YouTube Analytics API v2 Adapter.

Provides channel-level and video-level analytics, demographics,
traffic sources, and revenue data for the authenticated user's channel.

Uses the same OAuth credentials as the unified Google Workspace flow.
"""
from typing import Dict, Any, List

import structlog
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = structlog.get_logger(__name__)

# Scopes required (requested in the unified Workspace OAuth)
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]


class YouTubeAnalyticsAdapter:
    """
    Adapter for the YouTube Analytics API v2.

    All methods expect credentials_data from the Workspace OAuth flow
    (stored in ChannelConnection.credentials).
    """

    def __init__(self, credentials_data: Dict[str, Any]):
        self.creds = Credentials.from_authorized_user_info(credentials_data, SCOPES)

    def _get_analytics_service(self):
        return build("youtubeAnalytics", "v2", credentials=self.creds)

    def _get_data_service(self):
        """YouTube Data API v3 — used only to resolve the channel ID."""
        return build("youtube", "v3", credentials=self.creds)

    # ── Helpers ────────────────────────────────────────────────────────────

    def get_channel_id(self) -> str:
        """Resolves the authenticated user's channel ID via the Data API."""
        service = self._get_data_service()
        resp = service.channels().list(mine=True, part="id").execute()
        items = resp.get("items", [])
        if not items:
            raise ValueError("No se encontró un canal de YouTube para esta cuenta.")
        return items[0]["id"]

    def _query(
        self,
        start_date: str,
        end_date: str,
        metrics: str,
        dimensions: str = "",
        filters: str = "",
        sort: str = "",
        max_results: int = 0,
    ) -> Dict[str, Any]:
        """
        Low-level wrapper around reports().query().

        Returns the raw API response with columnHeaders and rows.
        """
        svc = self._get_analytics_service()
        params: dict = {
            "ids": "channel==MINE",
            "startDate": start_date,
            "endDate": end_date,
            "metrics": metrics,
        }
        if dimensions:
            params["dimensions"] = dimensions
        if filters:
            params["filters"] = filters
        if sort:
            params["sort"] = sort
        if max_results > 0:
            params["maxResults"] = max_results

        return svc.reports().query(**params).execute()

    @staticmethod
    def _rows_to_dicts(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts the columnHeaders + rows response into a list of dicts."""
        headers = [h["name"] for h in response.get("columnHeaders", [])]
        return [dict(zip(headers, row)) for row in response.get("rows", [])]

    # ── Public Methods ─────────────────────────────────────────────────────

    def get_channel_overview(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        Aggregate channel metrics for the given date range.

        Returns: views, estimatedMinutesWatched, averageViewDuration,
                 subscribersGained, subscribersLost, likes, dislikes,
                 comments, shares, averageViewPercentage.
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,dislikes,comments,shares,averageViewPercentage",
        )
        rows = self._rows_to_dicts(resp)
        return rows[0] if rows else {}

    def get_daily_views(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Daily breakdown of views and watch time.

        Useful for building time-series charts in the Growth Studio.
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration",
            dimensions="day",
            sort="day",
        )
        return self._rows_to_dicts(resp)

    def get_top_videos(
        self,
        start_date: str,
        end_date: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Top N videos by views in the date range.

        Returns video ID + views, likes, estimatedMinutesWatched.
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="views,likes,estimatedMinutesWatched,averageViewDuration",
            dimensions="video",
            sort="-views",
            max_results=max_results,
        )
        return self._rows_to_dicts(resp)

    def get_demographics(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Audience demographics: views broken down by ageGroup and gender.
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="viewerPercentage",
            dimensions="ageGroup,gender",
        )
        return self._rows_to_dicts(resp)

    def get_traffic_sources(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        Where the views are coming from (search, suggested, external, etc.).
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="views,estimatedMinutesWatched",
            dimensions="insightTrafficSourceType",
            sort="-views",
        )
        return self._rows_to_dicts(resp)

    def get_card_metrics(
        self,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        Card and end screen metrics for the channel.

        Returns: cardClicks, cardImpressions, endScreenElementClicks,
                 endScreenElementImpressions.
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="cardClicks,cardImpressions,endScreenElementClicks,endScreenElementImpressions",
        )
        rows = self._rows_to_dicts(resp)
        return rows[0] if rows else {}

    def get_top_videos_enriched(
        self,
        start_date: str,
        end_date: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Top videos with enriched metadata from the Data API v3.

        Combines Analytics API metrics (views, likes, watchTime) with
        Data API snippet (title, thumbnails, duration, publishedAt).
        """
        analytics_videos = self.get_top_videos(start_date, end_date, max_results)
        if not analytics_videos:
            return []

        video_ids = [v["video"] for v in analytics_videos if "video" in v]
        if not video_ids:
            return analytics_videos

        data_svc = self._get_data_service()
        snippet_resp = data_svc.videos().list(
            id=",".join(video_ids),
            part="snippet,contentDetails,statistics",
        ).execute()

        snippet_map: Dict[str, Dict[str, Any]] = {}
        for item in snippet_resp.get("items", []):
            vid = item["id"]
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = (
                thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )
            snippet_map[vid] = {
                "title": snippet.get("title", ""),
                "thumbnail_url": thumb_url,
                "duration": content.get("duration", ""),
                "published_at": snippet.get("publishedAt", ""),
            }

        enriched = []
        for v in analytics_videos:
            vid = v.get("video", "")
            meta = snippet_map.get(vid, {})
            enriched.append({
                "video_id": vid,
                "title": meta.get("title", ""),
                "thumbnail_url": meta.get("thumbnail_url", ""),
                "duration": meta.get("duration", ""),
                "published_at": meta.get("published_at", ""),
                "views": v.get("views", 0),
                "likes": v.get("likes", 0),
                "watch_time_minutes": v.get("estimatedMinutesWatched", 0),
                "avg_view_duration": v.get("averageViewDuration", 0),
            })

        return enriched

    def get_countries(
        self,
        start_date: str,
        end_date: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Views by country.
        """
        resp = self._query(
            start_date=start_date,
            end_date=end_date,
            metrics="views,estimatedMinutesWatched",
            dimensions="country",
            sort="-views",
            max_results=max_results,
        )
        return self._rows_to_dicts(resp)
