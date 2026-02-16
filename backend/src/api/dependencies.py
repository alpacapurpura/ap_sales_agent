from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
import structlog

import httpx
import os

from src.services.database import get_db
from src.core.security import verify_clerk_token
from src.services.db.models.user import User
from src.core.context import set_tenant_id
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.security import verify_clerk_token, verify_token_payload

logger = structlog.get_logger()

# Optional Security Scheme
security_optional = HTTPBearer(auto_error=False)

def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
) -> Optional[User]:
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
            
        user = db.query(User).filter(User.email == email).first()
        return user
    except Exception:
        return None

async def get_optional_tenant_context(
    user: Optional[User] = Depends(get_optional_current_user),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> Optional[UUID]:
    """
    Optional tenant context. Returns None if no user/tenant.
    """
    if not user:
        return None
        
    tenant_id = user.tenant_id
    if tenant_id:
        set_tenant_id(tenant_id)
        structlog.contextvars.bind_contextvars(tenant_id=str(tenant_id))
    
    return tenant_id

def get_current_user(
    db: Session = Depends(get_db),
    token_payload: Dict[str, Any] = Depends(verify_clerk_token),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> User:
    """
    Resolves the DB User from the Clerk Token.
    Uses 'email' claim to match User.email.
    Enforces Strict Tenant Isolation via X-Tenant-ID header.
    """
    # Clerk JWT structure varies. Checking standard claims.
    # 'sub' is the Clerk User ID.
    # 'email' is often a custom claim or under 'email_addresses'.
    # We will try 'email' top-level claim first (if configured in Clerk Session)
    # If not found, we might need to handle it.
    
    email = token_payload.get("email")
    if not email:
        # Fallback: Fetch from Clerk API using 'sub' (Clerk User ID)
        # This is slower but handles cases where JWT template is not configured.
        user_id = token_payload.get("sub")
        clerk_secret = os.getenv("CLERK_SECRET_KEY")
        
        if user_id and clerk_secret:
            try:
                logger.warning("fetching_email_from_clerk_api_fallback", user_id=user_id)
                # Synchronous call (blocking but necessary for fallback)
                resp = httpx.get(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers={"Authorization": f"Bearer {clerk_secret}"},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    clerk_user = resp.json()
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
            detail=f"Token missing email claim. Available claims: {available_keys}. Please configure Clerk JWT Template to include 'email'."
        )

    # Resolve User with strict Tenant Context
    query = db.query(User).filter(User.email == email)
    
    if x_tenant_id:
        try:
            # If header is present, we MUST match the tenant
            target_tenant_uuid = UUID(x_tenant_id)
            query = query.filter(User.tenant_id == target_tenant_uuid)
        except ValueError:
            logger.warning("invalid_tenant_header_format", header=x_tenant_id)
            # Invalid UUID -> User won't be found if we filter by it, 
            # or we ignore it. Safer to let the query fail to find a match.
            # We'll just pass here and let query.first() return None if strictly filtering logic was applied
            # But query.filter requires a valid UUID or expression.
            # Let's force a "False" condition to ensure 403
            # query = query.filter(text("1=0")) 
            # Simpler: just raise 400
            raise HTTPException(status_code=400, detail="Invalid X-Tenant-ID header format")

    user = query.first()
    
    if not user:
        # Enhanced Error Handling for Multi-Tenancy
        if x_tenant_id:
            # Check if user exists in ANY tenant to give specific error
            user_any = db.query(User).filter(User.email == email).first()
            if user_any:
                logger.warning("access_denied_tenant_mismatch", email=email, target_tenant=x_tenant_id)
                raise HTTPException(
                    status_code=403, 
                    detail="Acceso Denegado. Su usuario no pertenece al tenant solicitado."
                )
        
        logger.warning("access_denied_user_not_in_db", email=email)
        # STRICT ALLOWLIST POLICY:
        # The user must be pre-registered in the DB by an Admin.
        # We do NOT auto-create users anymore.
        raise HTTPException(
             status_code=403, 
             detail="Acceso Denegado. Su usuario no está registrado en nuestra base de datos. Por favor contacte a su administrador para solicitar acceso."
        )
        
    # Strict Tenant Validation (Double Check)
    if x_tenant_id and str(user.tenant_id) != x_tenant_id:
         # This should be caught by query filter, but safety net
         logger.error("security_invariant_violation_tenant_mismatch", user_id=str(user.id), header=x_tenant_id)
         raise HTTPException(status_code=403, detail="Security Violation: Tenant Mismatch")

    # Legacy check: User must have a tenant
    if not user.tenant_id:
         logger.warning("access_denied_no_tenant", user_id=str(user.id))
         raise HTTPException(
             status_code=403, 
             detail="No tiene los permisos suficientes para acceder a las funciones y que por favor se contacte con el administrador de su organización o, si quiere adquirir una suscripción se comunique a hola@alpacapurpura.lat"
         )
         
    return user

async def get_tenant_context(
    user: User = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> Optional[UUID]:
    """
    Determines Tenant ID and sets ContextVar.
    """
    tenant_id = user.tenant_id
    
    # Logic:
    # 1. If User has tenant_id, use it.
    # 2. If User is 'superuser' (logic TBD) and X-Tenant-ID is present, use that.
    
    # For now, simple logic:
    if tenant_id:
        set_tenant_id(tenant_id)
        # Bind to structlog context for observability
        structlog.contextvars.bind_contextvars(tenant_id=str(tenant_id))
    else:
        # If user has no tenant (e.g. Super Admin Global), we might not set context
        # Or we might want to fail if it's a tenant-scoped route.
        # For now, allow None (Global Context)
        pass
        
    return tenant_id

def get_current_tenant_id(user: User = Depends(get_current_user)) -> str:
    """
    Returns the tenant_id as string for dependency injection.
    Ensures user belongs to a tenant.
    """
    if not user.tenant_id:
         raise HTTPException(status_code=403, detail="User has no tenant")
    return str(user.tenant_id)
