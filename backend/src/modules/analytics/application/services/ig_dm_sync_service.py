"""Instagram DM Sync Service — manual backfill via Conversations API.

Calls GET /{page_id}/conversations?platform=instagram on the Facebook
Graph API to fetch historical DM conversations, then for each conversation
fetches messages. Each message is deduplicated by its `mid` (message_id)
against existing journey_events before inserting, ensuring idempotency
with webhook-created events.

Requires a Page Access Token (exchanged from the stored System User token)
and the `instagram_manage_messages` permission with Advanced Access.
"""

from datetime import UTC, datetime
from uuid import UUID

import httpx
import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.crm.application.services.identity_service import IdentityService
from src.modules.crm.application.services.ig_profile_enricher import (
    InstagramProfileEnricher,
)
from src.modules.crm.infrastructure.models.customer_model import (
    JourneyEventModel,
)
from src.modules.crm.infrastructure.repositories.customer_repository import (
    CustomerRepository,
    JourneyEventRepository,
)
from src.shared.domain.enums import IdentityType
from src.shared.domain.events import CHANNEL_TYPE_TO_CAPTURE_SLUG

logger = structlog.get_logger()

_GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class InstagramDMSyncService:
    """Sync historical Instagram DM conversations into journey_events."""

    def __init__(self, db: Session, connection_port: ConnectionPort):
        self.db = db
        self.connection_port = connection_port

    async def sync(self, tenant_id: UUID, max_conversations: int = 50) -> dict:
        """Sync IG DM conversations for a tenant.

        Returns: {"synced_messages": N, "new_leads": M, "skipped": K}
        """
        _zero = {"synced_messages": 0, "new_leads": 0, "skipped": 0}

        # Get Meta credentials
        creds = await self.connection_port.get_credentials(tenant_id, "meta")
        access_token = creds.credentials.get("access_token", "")
        if not access_token:
            logger.warning("ig_dm_sync_no_token", tenant_id=str(tenant_id))
            return _zero

        page_id = creds.config.get("tracked_page_id", "")
        if not page_id:
            logger.warning("ig_dm_sync_no_page_id", tenant_id=str(tenant_id))
            return _zero

        # Exchange System User token for Page Access Token
        page_token = await self._get_page_access_token(access_token, page_id)
        if not page_token:
            logger.warning("ig_dm_sync_page_token_failed", tenant_id=str(tenant_id))
            return _zero

        # Fetch conversations using Page Token and page_id
        conversations = await self._fetch_conversations(
            page_token,
            page_id,
            max_conversations,
        )

        synced = 0
        new_leads = 0
        skipped = 0

        capture_slug = CHANNEL_TYPE_TO_CAPTURE_SLUG.get("instagram", "ig-dm")
        customer_repo = CustomerRepository(self.db)
        identity_service = IdentityService(customer_repo)
        journey_repo = JourneyEventRepository(self.db)
        enricher = InstagramProfileEnricher(self.db)

        for conv in conversations:
            conv_id = conv.get("id", "")
            messages = await self._fetch_messages(conv_id, page_token)

            for msg in messages:
                mid = msg.get("id", "")
                if not mid:
                    continue

                # Dedup check: skip if journey_event with this message_id exists
                if self._message_exists(tenant_id, mid):
                    skipped += 1
                    continue

                sender = msg.get("from", {})
                sender_id = sender.get("id", "")
                if not sender_id:
                    continue

                # Skip echo messages (sent by the business)
                if sender_id == page_id:
                    continue

                # Get or create customer profile
                customer, was_created = identity_service.get_or_create_customer(
                    tenant_id=tenant_id,
                    identity_type=IdentityType.INSTAGRAM,
                    identity_value=sender_id,
                    profile_data={"traits": {}},
                    lead_source=capture_slug,
                    lead_source_detail="instagram",
                )

                if was_created:
                    new_leads += 1
                    # Enrich new profiles with IG user data
                    try:
                        await enricher.enrich(
                            tenant_id=tenant_id,
                            igsid=sender_id,
                            customer_profile_id=customer.id,
                            access_token=page_token,
                        )
                    except Exception:  # noqa: BLE001 — service resilience
                        logger.warning(
                            "ig_dm_sync_enrich_failed",
                            igsid=sender_id,
                            exc_info=True,
                        )

                # Parse message timestamp
                created_time = msg.get("created_time")
                occurred_at = (
                    datetime.fromisoformat(created_time)
                    if created_time
                    else datetime.now(UTC)
                )

                # Create journey_event with message_id for dedup
                journey_repo.track_event(
                    profile_id=customer.id,
                    tenant_id=tenant_id,
                    event_name="message_received",
                    event_type="track",
                    properties={
                        "channel_slug": capture_slug,
                        "channel_type": "instagram",
                        "message_direction": "inbound",
                        "message_id": mid,
                        "source": "ig_dm_sync",
                    },
                    occurred_at=occurred_at,
                )
                synced += 1

        self.db.commit()

        logger.info(
            "ig_dm_sync_complete",
            tenant_id=str(tenant_id),
            synced=synced,
            new_leads=new_leads,
            skipped=skipped,
        )
        return {"synced_messages": synced, "new_leads": new_leads, "skipped": skipped}

    def _message_exists(self, tenant_id: UUID, message_id: str) -> bool:
        """Check if a journey_event with this message_id already exists."""
        stmt = select(JourneyEventModel.id).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "message_received",
            func.jsonb_extract_path_text(JourneyEventModel.properties, "message_id")
            == message_id,
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    async def _get_page_access_token(self, system_user_token: str, page_id: str) -> str:
        """Exchange System User token for a Page Access Token."""
        url = f"{_GRAPH_API_BASE}/{page_id}"
        params = {"fields": "access_token", "access_token": system_user_token}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning(
                    "ig_dm_page_token_exchange_failed",
                    status=response.status_code,
                    body=response.text[:200],
                )
                return ""
            return response.json().get("access_token", "")
        except httpx.HTTPError:
            logger.warning("ig_dm_page_token_exchange_error", exc_info=True)
            return ""

    async def _fetch_conversations(
        self,
        page_token: str,
        page_id: str,
        limit: int,
    ) -> list[dict]:
        """Fetch IG DM conversations via Facebook Conversations API."""
        url = f"{_GRAPH_API_BASE}/{page_id}/conversations"
        params = {
            "platform": "instagram",
            "access_token": page_token,
            "limit": min(limit, 50),
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning(
                    "ig_conversations_fetch_failed",
                    status=response.status_code,
                    body=response.text[:300],
                )
                return []
            return response.json().get("data", [])
        except httpx.HTTPError:
            logger.warning("ig_conversations_fetch_error", exc_info=True)
            return []

    async def _fetch_messages(
        self,
        conversation_id: str,
        access_token: str,
    ) -> list[dict]:
        """Fetch messages for a single conversation."""
        url = f"{_GRAPH_API_BASE}/{conversation_id}/messages"
        params = {
            "fields": "id,created_time,from,message",
            "access_token": access_token,
            "limit": 100,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
            if response.status_code != 200:
                logger.warning(
                    "ig_messages_fetch_failed",
                    conversation_id=conversation_id,
                    status=response.status_code,
                )
                return []
            return response.json().get("data", [])
        except httpx.HTTPError:
            logger.warning(
                "ig_messages_fetch_error",
                conversation_id=conversation_id,
                exc_info=True,
            )
            return []
