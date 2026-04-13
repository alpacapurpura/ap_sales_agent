"""Instagram profile enricher via User Profile API.

When a user sends a DM via Instagram, we only have their IGSID (a numeric ID).
This service calls the Instagram User Profile API to fetch name, username,
profile_pic, follower_count, and follows_business — then updates the
CustomerProfile traits accordingly.

Permission required: instagram_business_manage_messages (already granted).
Restriction: only works for users who initiated a conversation (implicit consent).
"""

from uuid import UUID

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel

logger = structlog.get_logger()

# Fields to request from the Instagram User Profile API
_IG_PROFILE_FIELDS = "name,username,profile_pic,follower_count,is_user_follow_business"


class InstagramProfileEnricher:
    """Enriches a CustomerProfile with data from the Instagram User Profile API."""

    def __init__(self, db: Session):
        self.db = db

    async def enrich(
        self,
        tenant_id: UUID,
        igsid: str,
        customer_profile_id: UUID,
        access_token: str,
    ) -> str | None:
        """Fetch IG profile data and update customer traits.

        Returns the instagram_username if successfully fetched, None otherwise.
        """
        profile_data = await self._fetch_ig_profile(igsid, access_token)
        if not profile_data:
            return None

        username = profile_data.get("username")

        # Update the customer profile model directly
        profile_model = (
            self.db.execute(
                select(CustomerProfileModel).where(
                    CustomerProfileModel.id == customer_profile_id,
                    CustomerProfileModel.tenant_id == tenant_id,
                ),
            )
            .scalars()
            .first()
        )

        if not profile_model:
            return username

        current_traits = dict(profile_model.traits) if profile_model.traits else {}

        # Only set full_name if currently empty
        ig_name = profile_data.get("name")
        if ig_name and not profile_model.full_name:
            profile_model.full_name = ig_name

        # Always update IG-specific traits
        if username:
            current_traits["instagram_username"] = username
        if profile_data.get("profile_pic"):
            current_traits["profile_pic_url"] = profile_data["profile_pic"]
        if profile_data.get("follower_count") is not None:
            current_traits["follower_count"] = profile_data["follower_count"]
        if profile_data.get("is_user_follow_business") is not None:
            current_traits["follows_business"] = profile_data["is_user_follow_business"]

        profile_model.traits = current_traits
        self.db.flush()

        # Edge case: ManyChat arrived first and created a separate profile
        # with the same instagram_username. Merge that profile into this one.
        if username:
            self._merge_manychat_duplicate(tenant_id, customer_profile_id, username)

        logger.info(
            "ig_profile_enriched",
            tenant_id=str(tenant_id),
            igsid=igsid,
            username=username,
        )
        return username

    def _merge_manychat_duplicate(
        self,
        tenant_id: UUID,
        target_id: UUID,
        username: str,
    ) -> None:
        """If a ManyChat-created profile exists with same username, merge it."""
        from src.modules.crm.infrastructure.repositories.customer_repository import (
            CustomerRepository,
        )

        customer_repo = CustomerRepository(self.db)
        existing = customer_repo.find_by_trait(
            tenant_id=tenant_id,
            trait_key="instagram_username",
            trait_value=username,
        )
        if existing and existing.id != target_id:
            customer_repo.merge_profiles(
                source_id=existing.id,
                target_id=target_id,
                tenant_id=tenant_id,
            )

    async def _fetch_ig_profile(self, igsid: str, access_token: str) -> dict | None:
        """Call Instagram User Profile API for the given IGSID."""
        url = f"https://graph.instagram.com/v24.0/{igsid}"
        params = {"fields": _IG_PROFILE_FIELDS, "access_token": access_token}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)

            if response.status_code != 200:
                logger.warning(
                    "ig_profile_fetch_failed",
                    igsid=igsid,
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None

            return response.json()
        except Exception:
            logger.warning("ig_profile_fetch_error", igsid=igsid, exc_info=True)
            return None
