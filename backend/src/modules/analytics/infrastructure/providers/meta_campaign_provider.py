"""MetaCampaignProvider — extracts campaign hierarchy + recommendations from Meta API.

Separate from MetaProvider (metrics) to keep sync jobs independent.
Uses the same credential pattern (access_token, ad_account_id from ConnectionPort).
"""

import logging

import httpx

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"

logger = logging.getLogger(__name__)

_CAMPAIGN_FIELDS = (
    "id,name,objective,status,effective_status,bid_strategy,"
    "daily_budget,lifetime_budget,budget_remaining,buying_type,"
    "special_ad_categories,start_time,stop_time,"
    "created_time,updated_time"
)

_ADSET_FIELDS = (
    "id,campaign_id,name,status,effective_status,"
    "optimization_goal,billing_event,bid_strategy,"
    "daily_budget,lifetime_budget,budget_remaining,"
    "targeting,destination_type,learning_stage_info,"
    "start_time,end_time,recommendations"
)

_AD_FIELDS = (
    "id,campaign_id,adset_id,name,status,effective_status,"
    "creative{id,thumbnail_url,image_url,video_id,title,body,"
    "call_to_action_type,effective_object_story_id,url_tags},"
    "preview_shareable_link,recommendations"
)

_RECOMMENDATION_FIELDS = "recommendation_data{recommendation_signature,type,object_ids,recommendation_content,url}"


def _auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def _raise_for_meta_error(response: httpx.Response, context: str) -> None:
    if response.status_code >= 400:
        body = response.text[:500]
        logger.error(
            "meta_campaign_api_error context=%s status=%s body=%s",
            context,
            response.status_code,
            body,
        )
        response.raise_for_status()


async def _paginate(
    client: httpx.AsyncClient,
    url: str,
    headers: dict,
    params: dict,
    context: str,
    max_pages: int = 20,
) -> list[dict]:
    """Fetch all pages of a Meta API response."""
    all_data = []
    for _ in range(max_pages):
        resp = await client.get(url, headers=headers, params=params)
        _raise_for_meta_error(resp, context)
        body = resp.json()
        all_data.extend(body.get("data", []))

        paging = body.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break
        # Next URL is absolute — use it directly
        url = next_url
        params = {}  # params are embedded in the next URL
    return all_data


class MetaCampaignProvider:
    """Extracts campaign hierarchy and recommendations from Meta Marketing API."""

    async def extract_campaigns(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
    ) -> list[dict]:
        """Extract campaigns."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/campaigns",
            _auth_headers(access_token),
            {"fields": _CAMPAIGN_FIELDS, "limit": "500"},
            "campaigns",
        )

        campaigns = [
            {
                "external_id": row["id"],
                "name": row.get("name", ""),
                "objective": row.get("objective"),
                "status": row.get("status"),
                "effective_status": row.get("effective_status"),
                "bid_strategy": row.get("bid_strategy"),
                "daily_budget": int(row["daily_budget"]) if row.get("daily_budget") else None,
                "lifetime_budget": int(row["lifetime_budget"]) if row.get("lifetime_budget") else None,
                "budget_remaining": int(row["budget_remaining"]) if row.get("budget_remaining") else None,
                "buying_type": row.get("buying_type", "AUCTION"),
                "special_ad_categories": row.get("special_ad_categories", []),
                "start_time": row.get("start_time"),
                "stop_time": row.get("stop_time"),
                "external_created_time": row.get("created_time"),
                "external_updated_time": row.get("updated_time"),
            }
            for row in rows
        ]
        return campaigns

    async def extract_ad_sets(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
    ) -> tuple[list[dict], list[dict]]:
        """Return (ad_sets, inline_recommendations) tuple."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return [], []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/adsets",
            _auth_headers(access_token),
            {"fields": _ADSET_FIELDS, "limit": "500"},
            "adsets",
        )

        ad_sets = []
        inline_recs = []
        for row in rows:
            learning_info = row.get("learning_stage_info", {})
            ad_sets.append(
                {
                    "external_id": row["id"],
                    "campaign_external_id": row.get("campaign_id", ""),
                    "name": row.get("name", ""),
                    "status": row.get("status"),
                    "effective_status": row.get("effective_status"),
                    "optimization_goal": row.get("optimization_goal"),
                    "billing_event": row.get("billing_event"),
                    "bid_strategy": row.get("bid_strategy"),
                    "daily_budget": int(row["daily_budget"]) if row.get("daily_budget") else None,
                    "lifetime_budget": int(row["lifetime_budget"]) if row.get("lifetime_budget") else None,
                    "budget_remaining": int(row["budget_remaining"]) if row.get("budget_remaining") else None,
                    "targeting": row.get("targeting", {}),
                    "destination_type": row.get("destination_type"),
                    "learning_stage": learning_info.get("status") if learning_info else None,
                    "start_time": row.get("start_time"),
                    "end_time": row.get("end_time"),
                },
            )

            inline_recs.extend(
                {
                    "source": "ad_set",
                    "recommendation_type": str(rec.get("code", "")),
                    "object_ids": [row["id"]],
                    "title": rec.get("title"),
                    "body": rec.get("message"),
                    "blame_field": rec.get("blame_field"),
                    "importance": rec.get("importance"),
                    "confidence": rec.get("confidence"),
                }
                for rec in row.get("recommendations", [])
            )
        return ad_sets, inline_recs

    async def extract_ads(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
    ) -> tuple[list[dict], list[dict]]:
        """Return (ads, inline_recommendations) tuple."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return [], []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/ads",
            _auth_headers(access_token),
            {"fields": _AD_FIELDS, "limit": "500"},
            "ads",
        )

        ads = []
        inline_recs = []
        for row in rows:
            creative = row.get("creative", {})
            ads.append(
                {
                    "external_id": row["id"],
                    "campaign_external_id": row.get("campaign_id", ""),
                    "ad_set_external_id": row.get("adset_id", ""),
                    "name": row.get("name", ""),
                    "status": row.get("status"),
                    "effective_status": row.get("effective_status"),
                    "creative_id": creative.get("id"),
                    "creative_thumbnail_url": creative.get("thumbnail_url"),
                    "creative_image_url": creative.get("image_url"),
                    "creative_video_id": creative.get("video_id"),
                    "creative_title": creative.get("title"),
                    "creative_body": creative.get("body"),
                    "creative_cta": creative.get("call_to_action_type"),
                    "creative_link_url": None,  # Extracted from object_story_spec if needed
                    "preview_shareable_link": row.get("preview_shareable_link"),
                },
            )

            inline_recs.extend(
                {
                    "source": "ad",
                    "recommendation_type": str(rec.get("code", "")),
                    "object_ids": [row["id"]],
                    "title": rec.get("title"),
                    "body": rec.get("message"),
                    "blame_field": rec.get("blame_field"),
                    "importance": rec.get("importance"),
                    "confidence": rec.get("confidence"),
                }
                for rec in row.get("recommendations", [])
            )
        # Enrich video ads with high-resolution thumbnails
        await self._enrich_video_thumbnails(client, credentials, ads)

        return ads, inline_recs

    async def _enrich_video_thumbnails(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        ads: list[dict],
    ) -> None:
        """Fetch HD thumbnails for video ads (1080px vs default 64px).

        For each ad with a creative_video_id and no creative_image_url,
        fetches the first thumbnail from GET /{video_id}?fields=thumbnails.
        Stores the HD URL in creative_image_url so the service layer picks it.
        """
        access_token = credentials.get("access_token", "")
        video_ads = [a for a in ads if a.get("creative_video_id") and not a.get("creative_image_url")]
        if not video_ads:
            return

        for ad in video_ads:
            vid = ad["creative_video_id"]
            try:
                resp = await client.get(
                    f"{GRAPH_API_BASE}/{vid}",
                    headers=_auth_headers(access_token),
                    params={"fields": "thumbnails{uri,width,height}"},
                )
                if resp.status_code != 200:
                    continue
                thumbs = resp.json().get("thumbnails", {}).get("data", [])
                if thumbs:
                    ad["creative_image_url"] = thumbs[0]["uri"]
            except httpx.HTTPError:
                logger.debug("video_thumbnail_fetch_failed video_id=%s", vid)

    async def extract_account_recommendations(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
    ) -> list[dict]:
        """Extract account-level performance recommendations."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/recommendations",
            _auth_headers(access_token),
            {"fields": _RECOMMENDATION_FIELDS, "limit": "100"},
            "account_recommendations",
        )

        recs = []
        for row in rows:
            rec_data = row.get("recommendation_data", row)
            content = rec_data.get("recommendation_content", {})
            recs.append(
                {
                    "source": "account",
                    "recommendation_type": rec_data.get("type", "UNKNOWN"),
                    "object_ids": rec_data.get("object_ids", []),
                    "body": content.get("body"),
                    "lift_estimate": content.get("lift_estimate"),
                    "opportunity_score": content.get("opportunity_score_lift"),
                    "url": rec_data.get("url"),
                    "recommendation_signature": rec_data.get(
                        "recommendation_signature",
                    ),
                },
            )
        return recs
