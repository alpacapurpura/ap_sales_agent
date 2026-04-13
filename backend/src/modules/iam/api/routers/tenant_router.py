from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.application.services.tenant_service import TenantService
from src.modules.iam.domain.tenant import Tenant

router = APIRouter()


@router.get("/", response_model=list[Tenant])
async def list_tenants(db: Annotated[Session, Depends(get_db)]):
    """
    List all tenants (Admin only - TODO: Add admin protection).
    """
    service = TenantService(db)
    return service.get_all_tenants()


@router.post("/", response_model=Tenant)
async def create_tenant(
    name: str,
    slug: str,
    company_name: str,
    agent_persona: str,
    db: Annotated[Session, Depends(get_db)],
    can_use_keys: bool = False,
):
    """
    Create a new tenant.
    """
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
