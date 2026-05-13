"""Tenant Router API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from luana_core_iam.application.services.tenant_service import TenantService
from luana_core_iam.domain.tenant import Tenant
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/")
async def list_tenants(db: Annotated[Session, Depends(get_db)]) -> list[Tenant]:
    """List all tenants (Admin only - TODO: Add admin protection)."""
    service = TenantService(db)
    return service.get_all_tenants()


@router.post("/")
async def create_tenant(
    name: str,
    slug: str,
    company_name: str,
    agent_persona: str,
    db: Annotated[Session, Depends(get_db)],
    can_use_keys: bool = False,
) -> Tenant:
    """Create a new tenant."""
    service = TenantService(db)
    tenant, error = service.create_tenant(
        name=name,
        slug=slug,
        company_name=company_name,
        agent_persona=agent_persona,
        can_use_keys=can_use_keys,
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    return tenant
