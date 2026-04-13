"""CRM Referral API: code generation, listing, and evangelist promotion."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(prefix="/referrals", tags=["CRM - Referrals"])


# --- Request / Response Models ---


class PromoteRequest(BaseModel):
    customer_id: str  # UUID as string


class GenerateCodeRequest(BaseModel):
    customer_id: str  # UUID as string


class ReferralCodeResponse(BaseModel):
    id: str
    customer_id: str
    code: str
    source: str
    is_active: bool


class PromoteResponse(BaseModel):
    profile_id: str
    referral_code: str
    lifecycle_stage: str


# --- Endpoints ---


@router.get("", response_model=list[ReferralCodeResponse])
async def list_referral_codes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all active referral codes for tenant."""
    from src.modules.crm.application.services.referral_service import ReferralService

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


@router.post("/promote", response_model=PromoteResponse)
async def promote_to_evangelist(
    body: PromoteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Promote customer to EVANGELIST lifecycle stage + generate referral code.

    Uses LifecycleService.promote_to_evangelist atomically.
    """
    from src.modules.crm.application.services.lifecycle_service import LifecycleService

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


@router.post("/generate", response_model=ReferralCodeResponse)
async def generate_referral_code(
    body: GenerateCodeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate referral code for an existing evangelist who doesn't have one yet."""
    from src.modules.crm.application.services.referral_service import ReferralService

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
