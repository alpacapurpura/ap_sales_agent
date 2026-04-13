from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import structlog

from .base import BaseConnector

logger = structlog.get_logger()


class MailerliteConnector(BaseConnector):
    """
    Conector para sincronizar datos con MailerLite.
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._base_url = "https://connect.mailerlite.com/api"

    @staticmethod
    async def verify_connection(api_key: str) -> tuple[bool, dict[str, Any]]:
        """
        Verifica si la API Key es válida haciendo una llamada a /api/account.
        """
        url = "https://connect.mailerlite.com/api/account"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return True, response.json()
                return False, {
                    "error": f"Status: {response.status_code}, Body: {response.text}",
                }
        except Exception as e:
            return False, {"error": str(e)}

    async def get_recent_campaign_activity(
        self,
        hours: int = 7,
    ) -> list[dict[str, Any]]:
        """
        Fetch recent campaign subscriber activity (opens/clicks) from Mailerlite API.

        Used by the ETL backup sync to recover missed webhook events.

        Args:
            hours: Number of hours to look back for campaign activity.

        Returns:
            List of activity dicts with keys: email, campaign_id, campaign_name, event_type.
        """
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        activities: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
                # Fetch recent sent campaigns
                campaigns_url = (
                    f"{self._base_url}/campaigns"
                    f"?filter[status]=sent&sort=-finished_at&limit=25"
                )
                campaigns_resp = await client.get(campaigns_url)
                if campaigns_resp.status_code != 200:
                    logger.warning(
                        "Mailerlite campaigns API returned %s: %s",
                        campaigns_resp.status_code,
                        campaigns_resp.text[:200],
                    )
                    return []

                campaigns_data = campaigns_resp.json().get("data", [])
                # Filter campaigns finished within the cutoff window
                recent_campaigns = []
                for campaign in campaigns_data:
                    finished_at = campaign.get("finished_at")
                    if not finished_at:
                        continue
                    try:
                        finished_dt = datetime.fromisoformat(finished_at)
                    except (ValueError, TypeError):
                        continue
                    if finished_dt >= cutoff:
                        recent_campaigns.append(campaign)

                logger.info(
                    "Fetching Mailerlite campaign activity for last %d hours, found %d campaigns",
                    hours,
                    len(recent_campaigns),
                )

                # For each recent campaign, fetch opens and clicks
                for campaign in recent_campaigns:
                    campaign_id = campaign.get("id", "")
                    campaign_name = campaign.get("name", "")

                    for activity_type, event_type in [
                        ("opened", "open"),
                        ("clicked", "click"),
                    ]:
                        activity_url = (
                            f"{self._base_url}/campaigns/{campaign_id}"
                            f"/reports/subscriber-activity"
                            f"?filter[type]={activity_type}&limit=100"
                        )
                        activity_resp = await client.get(activity_url)
                        if activity_resp.status_code != 200:
                            logger.warning(
                                "Mailerlite subscriber-activity API returned %s for campaign %s (%s)",
                                activity_resp.status_code,
                                campaign_id,
                                activity_type,
                            )
                            continue

                        activity_data = activity_resp.json().get("data", [])
                        for entry in activity_data:
                            subscriber = entry.get("subscriber", {})
                            email = subscriber.get("email")
                            if not email:
                                continue
                            activities.append(
                                {
                                    "email": email,
                                    "campaign_id": str(campaign_id),
                                    "campaign_name": campaign_name,
                                    "event_type": event_type,
                                },
                            )

        except httpx.HTTPError as e:
            logger.warning(
                "Mailerlite API error during campaign activity fetch: %s",
                str(e),
            )
            return []
        except Exception as e:
            logger.warning(
                "Unexpected error fetching Mailerlite campaign activity: %s",
                str(e),
            )
            return []

        return activities

    def sync_contacts(self, tenant_id: str) -> list[dict[str, Any]]:
        # TODO: Implementar lógica real de MailerLite para obtener suscriptores
        logger.info("mailerlite_sync_contacts_started", tenant_id=tenant_id)
        return []

    def sync_events(self, tenant_id: str) -> list[dict[str, Any]]:
        # TODO: Implementar lógica real de MailerLite para obtener eventos (aperturas, clics, etc.)
        logger.info("mailerlite_sync_events_started", tenant_id=tenant_id)
        return []


# Alias for CamelCase import used in tasks.py (MailerLiteConnector vs MailerliteConnector)
MailerLiteConnector = MailerliteConnector
