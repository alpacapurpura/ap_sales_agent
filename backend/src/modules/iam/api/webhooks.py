"""Webhooks API endpoints."""

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from luana_core_iam.domain.user import User
from luana_core_iam.infrastructure.repositories.user_repository import UserRepository
from luana_core_platform.core.config import settings
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session
from svix.webhooks import Webhook, WebhookVerificationError

router = APIRouter()
logger = structlog.get_logger()


async def _handle_user_sync(repo: UserRepository, data: dict, event_type: str) -> None:
    """Synchronize user data from Clerk to local DB."""
    clerk_id = data.get("id")
    email_addresses = data.get("email_addresses", [])
    primary_email_id = data.get("primary_email_address_id")

    # Find primary email
    email = ""
    for email_obj in email_addresses:
        if email_obj.get("id") == primary_email_id:
            email = email_obj.get("email_address")
            break

    # Fallback to first email if primary not found
    if not email and email_addresses:
        email = email_addresses[0].get("email_address")

    first_name = data.get("first_name") or ""
    last_name = data.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip()

    # 1. Try to find by Clerk ID (Best Match)
    existing_user = repo.get_by_clerk_id(clerk_id)

    # 2. Fallback: Try to find by Email (Legacy/Migration)
    # If found by email but no clerk_id, we should link them.
    if not existing_user and email:
        existing_user_by_email = repo.get_by_email(email)
        if existing_user_by_email:
            logger.info("clerk_user_linked_by_email", email=email, clerk_id=clerk_id)
            existing_user = existing_user_by_email

    if event_type == "user.created" and not existing_user:
        # Create new user
        new_user = User(
            id=uuid.uuid4(),
            full_name=full_name,
            email=email,
            clerk_id=clerk_id,
            is_active=True,
            role="user",  # Default role
        )
        repo.create(new_user)
        logger.info("clerk_user_synced_created", email=email, clerk_id=clerk_id)

    elif existing_user:
        # Update existing user
        existing_user.full_name = full_name
        existing_user.email = email
        existing_user.clerk_id = clerk_id  # Ensure clerk_id is always set/updated
        repo.update(existing_user)
        logger.info("clerk_user_synced_updated", email=email, clerk_id=clerk_id)


async def _handle_user_deletion(repo: UserRepository, data: dict) -> None:
    """Soft deletes user when deleted in Clerk."""
    clerk_id = data.get("id")
    user = repo.get_by_clerk_id(clerk_id)

    if user:
        user.is_active = False
        repo.update(user)
        logger.info("clerk_user_deactivated", clerk_id=clerk_id)
    else:
        logger.warning("clerk_user_delete_not_found", clerk_id=clerk_id)


@router.post("/clerk", status_code=status.HTTP_200_OK)
async def clerk_webhook_handler(request: Request, db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Handle incoming webhooks from Clerk (User Created, Updated, Deleted).

    Verifies the signature using Svix.
    """
    # 1. Get Headers
    headers = request.headers
    payload = await request.body()

    svix_id = headers.get("svix-id")
    svix_timestamp = headers.get("svix-timestamp")
    svix_signature = headers.get("svix-signature")

    if not all([svix_id, svix_timestamp, svix_signature]):
        logger.warning("clerk_webhook_missing_headers", headers=headers)
        raise HTTPException(status_code=400, detail="Missing svix headers")

    # 2. Verify Signature
    if not settings.CLERK_WEBHOOK_SECRET:
        logger.error("clerk_webhook_secret_missing")
        # Fail gracefully if not configured to avoid spamming Clerk with 500s?
        # No, better to 500 so we know it's broken.
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    wh = Webhook(settings.CLERK_WEBHOOK_SECRET)
    try:
        # verify returns the event payload as a dict
        evt = wh.verify(payload, headers)
    except WebhookVerificationError as e:
        logger.exception("clerk_webhook_verification_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    # 3. Process Event
    data = evt.get("data", {})
    event_type = evt.get("type")
    user_repo = UserRepository(db)

    logger.info(
        "clerk_webhook_received",
        event_type=event_type,
        clerk_id=data.get("id"),
    )

    try:
        if event_type in ["user.created", "user.updated"]:
            await _handle_user_sync(user_repo, data, event_type)
        elif event_type == "user.deleted":
            await _handle_user_deletion(user_repo, data)
        else:
            logger.info("clerk_webhook_ignored_type", event_type=event_type)

    except Exception as e:
        logger.exception(
            "clerk_webhook_processing_error",
            error=str(e),
            event_type=event_type,
        )
        # We catch internal errors to avoid retrying if it's a logic error,
        # but for now let's raise 500 to let Clerk retry network blips.
        raise HTTPException(status_code=500, detail="Error processing webhook") from e

    return {"status": "success"}
