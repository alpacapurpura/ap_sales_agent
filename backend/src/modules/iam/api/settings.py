"""Settings API endpoints."""

import secrets
import string
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.tenant import (
    AISettings,
    GeneralSettings,
    GeneralSettingsUpdate,
    TenantProfile,
    TenantSettingsUpdate,
    WebhookSettings,
)
from luana_core_iam.domain.user import (
    SystemUserProfile,
    TeamMemberCreate,
    TeamMemberSchema,
    User,
)
from luana_core_iam.infrastructure.models import (
    TenantModel,
    UserModel,
    UserTenantModel,
)
from luana_core_platform.core.config import settings as app_settings
from luana_core_platform.core.database import get_db
from luana_core_platform.infrastructure.external.clerk import ClerkService
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = structlog.get_logger()

router = APIRouter()


def generate_secret_key(length: int = 32) -> str:
    """Handle generate secret key request."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(length))


@router.get("/general")
async def get_general_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneralSettings:
    """Get current General configuration for the user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    tenant = db.execute(select(TenantModel).where(TenantModel.id == current_user.tenant_id)).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return GeneralSettings(
        default_currency=tenant.default_currency or "USD",
        timezone=tenant.timezone or "UTC",
    )


@router.patch("/general")
async def update_general_settings(
    settings: GeneralSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GeneralSettings:
    """Update General configuration for the user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    tenant = db.execute(select(TenantModel).where(TenantModel.id == current_user.tenant_id)).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if settings.default_currency is not None:
        tenant.default_currency = settings.default_currency

    if settings.timezone is not None:
        tenant.timezone = settings.timezone

    db.commit()
    db.refresh(tenant)

    return GeneralSettings(
        default_currency=tenant.default_currency or "USD",
        timezone=tenant.timezone or "UTC",
    )


@router.get("/ai")
async def get_ai_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AISettings:
    """Get current AI configuration for the user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    tenant = db.execute(select(TenantModel).where(TenantModel.id == current_user.tenant_id)).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # T-6a: only ``gemini_api_key`` is still active. The 4 deprecated cols
    # (openai/deepseek/kimi/dashscope) are NULLed by the T-6a migration
    # and excluded from the AISettings response model — passing them to
    # the constructor would emit DeprecationWarnings without any effect
    # on the rendered response.
    return AISettings(
        gemini_api_key=tenant.gemini_api_key,
        can_use_platform_keys=tenant.can_use_platform_keys or False,
    )


@router.get("/profile")
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SystemUserProfile:
    """Get current user profile and tenant info."""
    logger.info(
        "get_user_profile_called",
        user_email=current_user.email,
        context_tenant_id=str(current_user.tenant_id) if hasattr(current_user, "tenant_id") else "None",
    )

    tenant_profile = None
    if getattr(current_user, "tenant_id", None):
        tenant = (
            db.execute(
                select(TenantModel).where(TenantModel.id == current_user.tenant_id),
            )
            .scalars()
            .first()
        )
        if tenant:
            logger.info(
                "tenant_resolved_for_profile",
                tenant_name=tenant.name,
                tenant_id=str(tenant.id),
            )
            tenant_profile = TenantProfile(
                id=str(tenant.id),
                name=tenant.name,
                slug=tenant.slug,
                timezone=tenant.timezone or "UTC",
            )
        else:
            logger.warning(
                "tenant_not_found_for_profile",
                tenant_id=str(current_user.tenant_id),
            )

    return SystemUserProfile(
        id=str(current_user.id),
        full_name=current_user.full_name,
        email=current_user.email,
        tenant=tenant_profile,
    )


@router.get("/webhook")
async def get_webhook_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WebhookSettings:
    """Get Webhook configuration for the user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    tenant = db.execute(select(TenantModel).where(TenantModel.id == current_user.tenant_id)).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Construct URL from API_DOMAIN (required in .env)
    domain = app_settings.API_DOMAIN
    if not domain:
        raise HTTPException(
            status_code=500,
            detail="API_DOMAIN not configured on server",
        )
    protocol = "https" if not domain.startswith("localhost") else "http"
    webhook_url = f"{protocol}://{domain}/api/v1/webhook/chat"

    return WebhookSettings(
        webhook_url=webhook_url,
        webhook_secret=tenant.webhook_secret,
    )


@router.post("/webhook/regenerate")
async def regenerate_webhook_secret(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> WebhookSettings:
    """Regenerate Webhook Secret for the user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    tenant = db.execute(select(TenantModel).where(TenantModel.id == current_user.tenant_id)).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Generate new secret (n8n style)
    new_secret = f"sk_live_{generate_secret_key()}"
    tenant.webhook_secret = new_secret

    db.commit()
    db.refresh(tenant)

    domain = app_settings.API_DOMAIN
    if not domain:
        raise HTTPException(
            status_code=500,
            detail="API_DOMAIN not configured on server",
        )
    protocol = "https" if not domain.startswith("localhost") else "http"
    webhook_url = f"{protocol}://{domain}/api/v1/webhook/chat"

    return WebhookSettings(
        webhook_url=webhook_url,
        webhook_secret=tenant.webhook_secret,
    )


@router.patch("/ai")
async def update_ai_settings(
    settings: TenantSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AISettings:
    """Update AI API Keys for the user's tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    tenant = db.execute(select(TenantModel).where(TenantModel.id == current_user.tenant_id)).scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # T-6a: deprecated provider keys (openai/deepseek/kimi/dashscope) are
    # accepted by the request schema for backward compatibility but
    # silently ignored — the columns are NULL post-T-6a migration and
    # write-paths are removed. ``gemini_api_key`` remains writable.
    if settings.gemini_api_key is not None:
        tenant.gemini_api_key = settings.gemini_api_key

    db.commit()
    db.refresh(tenant)

    return AISettings(
        gemini_api_key=tenant.gemini_api_key,
        can_use_platform_keys=tenant.can_use_platform_keys or False,
    )


@router.get("/team")
async def get_team_members(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TeamMemberSchema]:
    """List all team members for the current tenant."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    # FIX: Query User via UserTenant M:N table
    users = (
        db.execute(
            select(UserModel)
            .join(UserTenantModel)
            .where(
                UserTenantModel.tenant_id == current_user.tenant_id,
                UserTenantModel.is_active.is_(True),
            )
            .order_by(UserModel.created_at),
        )
        .scalars()
        .all()
    )

    # We need to get the role from UserTenant for each user relative to THIS tenant
    # The simple query above returns User objects, but their 'role' field is global (legacy) or potentially confusing.
    # Ideally, we should fetch (User, UserTenant.role).

    results = []
    for u in users:
        # Fetch the specific role for this tenant
        link = (
            db.execute(
                select(UserTenantModel).where(
                    UserTenantModel.user_id == u.id,
                    UserTenantModel.tenant_id == current_user.tenant_id,
                    UserTenantModel.is_active.is_(True),
                ),
            )
            .scalars()
            .first()
        )

        role = link.role if link else "member"

        results.append(
            TeamMemberSchema(
                id=str(u.id),
                full_name=u.full_name,
                email=u.email,
                role=role,
                is_active=u.is_active,
                created_at=u.created_at,
            ),
        )

    return results


@router.post("/team")
async def create_team_member(
    user_in: TeamMemberCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TeamMemberSchema:
    """Create a new user for the team (Max 3 users total)."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    # Check limit
    # Max 3 users total (Admin + 2).
    count = db.execute(
        select(func.count(UserTenantModel.user_id)).where(
            UserTenantModel.tenant_id == current_user.tenant_id,
            UserTenantModel.is_active.is_(True),
        ),
    ).scalar()
    if count >= 3:
        raise HTTPException(
            status_code=403,
            detail="Límite de usuarios alcanzado (Máximo 3 por plan).",
        )

    # Check email usage locally
    existing_user = db.execute(select(UserModel).where(UserModel.email == user_in.email)).scalars().first()
    if existing_user:
        # Check if already in tenant
        if (
            db.execute(
                select(UserTenantModel).where(
                    UserTenantModel.user_id == existing_user.id,
                    UserTenantModel.tenant_id == current_user.tenant_id,
                    UserTenantModel.is_active.is_(True),
                ),
            )
            .scalars()
            .first()
        ):
            raise HTTPException(
                status_code=400,
                detail="El email ya está registrado en este equipo.",
            )
        # Link existing user? For now, simplistic approach: Fail if email exists globally to avoid confusion
        # (unless we want to support multi-tenant invites here).
        # Let's support linking for better UX if they exist but not in this tenant.
        # Actually, simpler to just raise error for now as per original logic,
        # or create the link if we want to be fancy. Let's stick to safe defaults.
        raise HTTPException(
            status_code=400,
            detail="El usuario ya existe en el sistema. Contacte al soporte para añadirlo.",
        )

    # Create in Clerk
    clerk = ClerkService()
    clerk_user_id = None
    try:
        # Create in Clerk
        clerk_resp = clerk.create_user(
            user_in.email,
            user_in.password,
            user_in.full_name,
        )
        clerk_user_id = clerk_resp.get("id")

        if clerk_user_id:
            clerk.update_user_metadata(
                clerk_user_id,
                {"tenant_id": str(current_user.tenant_id), "role": "member"},
            )

    except Exception as e:
        if "ya existe" in str(e):
            raise HTTPException(
                status_code=400,
                detail="El usuario ya existe en el sistema de identidad.",
            ) from e
        raise HTTPException(
            status_code=500,
            detail=f"Error creando usuario en Clerk: {e!s}",
        ) from e

    # Create DB User
    # FIX: Remove tenant_id from User constructor
    new_user = UserModel(
        email=user_in.email,
        full_name=user_in.full_name,
        # tenant_id=current_user.tenant_id,  <-- REMOVED
        clerk_id=clerk_user_id,
        role="member",
        is_active=True,
    )
    db.add(new_user)
    db.flush()  # Get ID

    # Create Link
    new_link = UserTenantModel(
        user_id=new_user.id,
        tenant_id=current_user.tenant_id,
        role="member",
    )
    db.add(new_link)

    db.commit()
    db.refresh(new_user)

    return TeamMemberSchema(
        id=str(new_user.id),
        full_name=new_user.full_name,
        email=new_user.email,
        role="member",
        is_active=new_user.is_active,
        created_at=new_user.created_at,
    )
