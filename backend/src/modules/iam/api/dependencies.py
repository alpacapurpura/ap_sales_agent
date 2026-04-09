import os
from typing import Any
from uuid import UUID

import httpx
import structlog
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.context import set_tenant_id
from src.core.database import get_db
from src.modules.iam.application.auth import verify_clerk_token, verify_token_payload
from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models import (
    TenantModel,
    UserModel,
    UserTenantModel,
)
from src.shared.domain.locale import TenantLocale

logger = structlog.get_logger()

# Optional Security Scheme
security_optional = HTTPBearer(auto_error=False)


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
) -> User | None:
    """
    Returns User if token is present and valid, else None.
    Does NOT raise 401/403 for missing token.
    """
    if not credentials:
        return None

    try:
        # Manually call verify logic
        payload = verify_token_payload(credentials.credentials)

        # Resolve User (Copy-paste logic from get_current_user roughly, or refactor)
        # Refactoring get_current_user to be reusable would be best, but for speed:
        email = payload.get("email")
        if not email:
            # Simplistic fallback for optional auth
            return None

        user = (
            db.execute(select(UserModel).where(UserModel.email == email))
            .scalars()
            .first()
        )
        if user:
            return User.model_validate(user)
        return None
    except Exception:
        return None


async def get_optional_tenant_context(
    user: User | None = Depends(get_optional_current_user),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    db: Session = Depends(get_db),
) -> UUID | None:
    """
    Optional tenant context. Returns None if no user/tenant.
    """
    if not user:
        return None

    tenant_id = None

    # Try X-Tenant-ID
    if x_tenant_id:
        try:
            target_uuid = UUID(x_tenant_id)
            # Check access
            link = (
                db.execute(
                    select(UserTenantModel).where(
                        UserTenantModel.user_id == user.id,
                        UserTenantModel.tenant_id == target_uuid,
                        UserTenantModel.is_active.is_(True),
                    )
                )
                .scalars()
                .first()
            )
            if link:
                tenant_id = target_uuid
        except ValueError:
            # Try to resolve by slug
            tenant = (
                db.execute(select(TenantModel).where(TenantModel.slug == x_tenant_id))
                .scalars()
                .first()
            )
            if tenant:
                link = (
                    db.execute(
                        select(UserTenantModel).where(
                            UserTenantModel.user_id == user.id,
                            UserTenantModel.tenant_id == tenant.id,
                            UserTenantModel.is_active.is_(True),
                        )
                    )
                    .scalars()
                    .first()
                )
                if link:
                    tenant_id = tenant.id

    # Fallback to default
    if not tenant_id:
        link = (
            db.execute(
                select(UserTenantModel).where(
                    UserTenantModel.user_id == user.id,
                    UserTenantModel.is_active.is_(True),
                )
            )
            .scalars()
            .first()
        )
        if link:
            tenant_id = link.tenant_id

    if tenant_id:
        # Set dynamic attribute
        user.tenant_id = tenant_id
        set_tenant_id(tenant_id)
        structlog.contextvars.bind_contextvars(tenant_id=str(tenant_id))

    return tenant_id


def get_user_from_token(
    db: Session = Depends(get_db),
    token_payload: dict[str, Any] = Depends(verify_clerk_token),
) -> User:
    """
    Core dependency to resolve User from Token.
    Does NOT check Tenant Context.
    """
    # Clerk JWT structure varies. Checking standard claims.
    # 'sub' is the Clerk User ID.
    # 'email' is often a custom claim or under 'email_addresses'.
    # We will try 'email' top-level claim first (if configured in Clerk Session)
    # If not found, we might need to handle it.

    email = token_payload.get("email")
    clerk_user_data = None

    if not email:
        # Fallback: Fetch from Clerk API using 'sub' (Clerk User ID)
        # This is slower but handles cases where JWT template is not configured.
        user_id = token_payload.get("sub")
        clerk_secret = os.getenv("CLERK_SECRET_KEY")

        if user_id and clerk_secret:
            try:
                logger.warning(
                    "fetching_email_from_clerk_api_fallback", user_id=user_id
                )
                # Synchronous call (blocking but necessary for fallback)
                resp = httpx.get(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers={"Authorization": f"Bearer {clerk_secret}"},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    clerk_user = resp.json()
                    clerk_user_data = clerk_user
                    # Try to find primary email
                    email_addresses = clerk_user.get("email_addresses", [])
                    primary_id = clerk_user.get("primary_email_address_id")

                    for e in email_addresses:
                        if e.get("id") == primary_id:
                            email = e.get("email_address")
                            break

                    # If not found, take the first one
                    if not email and email_addresses:
                        email = email_addresses[0].get("email_address")

                    if email:
                        logger.info("email_resolved_via_clerk_api", email=email)
            except Exception as e:
                logger.error("clerk_api_fallback_failed", error=str(e))

    if not email:
        # Fallback failed or not possible
        available_keys = ", ".join(token_payload.keys())
        logger.error("token_payload_missing_email", keys=list(token_payload.keys()))
        raise HTTPException(
            status_code=401,
            detail=f"Token missing email claim. Available claims: {available_keys}. Please configure Clerk JWT Template to include 'email'.",
        )

    # Resolve User
    user_orm = (
        db.execute(select(UserModel).where(UserModel.email == email)).scalars().first()
    )

    if not user_orm:
        logger.warning("access_denied_user_not_in_db", email=email)
        raise HTTPException(
            status_code=403,
            detail="Acceso Denegado. Su usuario no está registrado en nuestra base de datos. Por favor contacte a su administrador para solicitar acceso.",
        )

    # Sync Clerk ID and Full Name if needed
    clerk_id_from_token = token_payload.get("sub")

    # Try to get name from token
    name_from_token = token_payload.get("name")
    if not name_from_token:
        # Construct from given/family name
        given = token_payload.get("given_name", "")
        family = token_payload.get("family_name", "")
        if given or family:
            name_from_token = f"{given} {family}".strip()

    # If not in token, try fallback data
    if not name_from_token and clerk_user_data:
        first = clerk_user_data.get("first_name", "")
        last = clerk_user_data.get("last_name", "")
        if first or last:
            name_from_token = f"{first} {last}".strip()

    if clerk_id_from_token:
        should_update = False

        # Check Clerk ID mismatch
        if user_orm.clerk_id != clerk_id_from_token:
            logger.info(
                "updating_user_clerk_id",
                email=email,
                old_id=user_orm.clerk_id,
                new_id=clerk_id_from_token,
            )
            user_orm.clerk_id = clerk_id_from_token
            should_update = True

        # Check Full Name
        if name_from_token and user_orm.full_name != name_from_token:
            logger.info(
                "updating_user_full_name",
                email=email,
                old_name=user_orm.full_name,
                new_name=name_from_token,
            )
            user_orm.full_name = name_from_token
            should_update = True

        if should_update:
            db.add(user_orm)
            db.commit()
            db.refresh(user_orm)

    return User.model_validate(user_orm)


def get_current_user_global(user: User = Depends(get_user_from_token)) -> User:
    """
    Returns the current user WITHOUT enforcing tenant context.
    Useful for endpoints that list tenants or user settings.
    """
    return user


def get_current_user(
    db: Session = Depends(get_db),
    user: User = Depends(get_user_from_token),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> User:
    """
    Resolves the DB User and Enforces Strict Tenant Isolation via X-Tenant-ID header.
    """
    email = user.email

    # Multi-Tenant Logic
    # Check if X-Tenant-ID is provided
    target_tenant_id = None

    # DEBUG LOG
    logger.info("resolving_tenant_context", email=email, header_x_tenant_id=x_tenant_id)

    if x_tenant_id:
        try:
            target_tenant_id = UUID(x_tenant_id)
        except ValueError:
            # Try to resolve by slug
            tenant = (
                db.execute(select(TenantModel).where(TenantModel.slug == x_tenant_id))
                .scalars()
                .first()
            )
            if not tenant:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid X-Tenant-ID header format (UUID or Slug)",
                )
            target_tenant_id = tenant.id

        # Verify user has access to this tenant
        user_tenant = (
            db.execute(
                select(UserTenantModel).where(
                    UserTenantModel.user_id == user.id,
                    UserTenantModel.tenant_id == target_tenant_id,
                    UserTenantModel.is_active.is_(True),
                )
            )
            .scalars()
            .first()
        )

        if not user_tenant:
            logger.warning(
                "access_denied_tenant_mismatch", email=email, target_tenant=x_tenant_id
            )
            raise HTTPException(
                status_code=403,
                detail="Acceso Denegado. Su usuario no pertenece al tenant solicitado.",
            )

        # Set the dynamic attribute for downstream use
        user.tenant_id = target_tenant_id
        # Also set the role for this tenant context if needed
        user.role = user_tenant.role

        logger.info("tenant_context_set_from_header", tenant_id=str(user.tenant_id))

    else:
        # No tenant specified. Find the first available tenant for the user.
        # This is the "default" tenant context.
        first_tenant_link = (
            db.execute(
                select(UserTenantModel).where(
                    UserTenantModel.user_id == user.id,
                    UserTenantModel.is_active.is_(True),
                )
            )
            .scalars()
            .first()
        )

        if not first_tenant_link:
            logger.warning("access_denied_no_tenants", user_id=str(user.id))
            raise HTTPException(
                status_code=403,
                detail="No tiene ninguna organización asignada. Contacte al soporte.",
            )

        user.tenant_id = first_tenant_link.tenant_id
        user.role = first_tenant_link.role

        logger.info("tenant_context_set_default", tenant_id=str(user.tenant_id))

    return user


async def get_tenant_context(
    user: User = Depends(get_current_user),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> UUID | None:
    """
    Determines Tenant ID and sets ContextVar.
    """
    tenant_id = user.tenant_id

    if tenant_id:
        set_tenant_id(tenant_id)
        # Bind to structlog context for observability
        structlog.contextvars.bind_contextvars(tenant_id=str(tenant_id))

    return tenant_id


def get_current_tenant_id(user: User = Depends(get_current_user)) -> str:
    """
    Returns the tenant_id as string for dependency injection.
    Ensures user belongs to a tenant.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="User has no tenant")
    return str(user.tenant_id)


def _resolve_tenant_locale(db: Session, tenant_id: UUID) -> TenantLocale:
    """Load TenantLocale from DB. Extracted for testability."""
    tenant = (
        db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
        .scalars()
        .first()
    )
    if tenant:
        return TenantLocale(
            currency=tenant.default_currency or "USD",
            timezone=tenant.timezone or "UTC",
        )
    return TenantLocale.default()


def get_tenant_locale(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TenantLocale:
    """FastAPI dependency: resolves TenantLocale for the current request.

    The tenant row is typically already in the SA session identity map
    from get_current_user, so this is a cache hit, not a new query.
    """
    return _resolve_tenant_locale(db, user.tenant_id)
