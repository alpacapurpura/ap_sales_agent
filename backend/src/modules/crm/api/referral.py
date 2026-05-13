"""CRM Referral API: code generation, listing, and evangelist promotion."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/referrals", tags=["CRM - Referrals"])


# --- Request / Response Models ---


class PromoteRequest(BaseModel):
    """Request schema for promote."""

    customer_id: str  # UUID as string


class GenerateCodeRequest(BaseModel):
    """Request schema for generate code."""

    customer_id: str  # UUID as string


class ReferralCodeResponse(BaseModel):
    """Response schema for referral code."""

    id: str
    customer_id: str
    code: str
    source: str
    is_active: bool


class PromoteResponse(BaseModel):
    """Response schema for promote."""

    profile_id: str
    referral_code: str
    lifecycle_stage: str


# --- Endpoints ---


@router.get("")
async def list_referral_codes(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ReferralCodeResponse]:
    """List all active referral codes for tenant."""
    from luana_core_crm.application.services.referral_service import ReferralService

    svc = ReferralService(db)
    codes = svc.get_codes_by_tenant(user.tenant_id, active_only=True)

    return [
        ReferralCodeResponse(
            id=str(c.id),
            customer_id=str(c.customer_id),
            code=c.code,
            source=c.source or "internal",
            is_active=c.is_active,
        )
        for c in codes
    ]


@router.post("/promote")
async def promote_to_evangelist(
    body: PromoteRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> PromoteResponse:
    """Promote customer to EVANGELIST lifecycle stage + generate referral code.

    Uses LifecycleService.promote_to_evangelist atomically.
    """
    from luana_core_crm.application.services.lifecycle_service import LifecycleService

    try:
        customer_id = UUID(body.customer_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid customer_id format",
        ) from None

    svc = LifecycleService(db)
    try:
        profile, referral_code = svc.promote_to_evangelist(
            profile_id=customer_id,
            tenant_id=user.tenant_id,
            reason="manual_promotion",
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return PromoteResponse(
        profile_id=str(profile.id),
        referral_code=referral_code.code,
        lifecycle_stage=profile.lifecycle_stage.value,
    )


@router.post("/generate")
async def generate_referral_code(
    body: GenerateCodeRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ReferralCodeResponse:
    """Generate referral code for an existing evangelist who doesn't have one yet."""
    from luana_core_crm.application.services.referral_service import ReferralService

    try:
        customer_id = UUID(body.customer_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid customer_id format",
        ) from None

    svc = ReferralService(db)

    # Check if customer already has a code
    existing = svc.get_code_by_customer(user.tenant_id, customer_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Customer already has referral code: {existing.code}",
        )

    code = svc.generate_code(user.tenant_id, customer_id)
    db.commit()

    return ReferralCodeResponse(
        id=str(code.id),
        customer_id=str(code.customer_id),
        code=code.code,
        source=code.source or "internal",
        is_active=code.is_active,
    )
