from typing import List
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.domains.api.domain_dtos import (
    DomainCreate,
    DomainInstructionsResponse,
    DomainResponse,
    DomainSetPrimary,
    DnsRecord,
)
from src.modules.domains.application.domain_service import DomainService
from src.modules.domains.domain.domain_entity import DomainType
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger()

router = APIRouter()


def _to_response(domain) -> DomainResponse:
    return DomainResponse(
        id=domain.id,
        tenant_id=domain.tenant_id,
        hostname=domain.hostname,
        domain_type=domain.domain_type,
        status=domain.status,
        is_primary=domain.is_primary,
        ssl_status=domain.ssl_status,
        verification_method=domain.verification_method,
        verification_cname_target=domain.verification_cname_target,
        verification_txt_name=domain.verification_txt_name,
        verification_txt_value=domain.verification_txt_value,
        verified_at=domain.verified_at,
        created_at=domain.created_at,
    )


@router.post("/", response_model=DomainResponse, status_code=201)
async def create_domain(
    body: DomainCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DomainResponse:
    service = DomainService(db)
    try:
        if body.domain_type == DomainType.PLATFORM:
            # hostname is the slug for platform domains
            domain = service.create_platform_domain(
                tenant_id=user.tenant_id,
                slug=body.hostname,
            )
        else:
            conflict = service.detect_domain_conflict(body.hostname)
            if conflict:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "DOMAIN_CONFLICT",
                        "provider": conflict["provider"],
                        "suggestion": conflict["suggestion"],
                        "message": conflict["message"],
                    },
                )
            domain = service.create_custom_domain(
                tenant_id=user.tenant_id,
                hostname=body.hostname,
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("domain_create_failed", tenant_id=str(user.tenant_id))
        raise HTTPException(status_code=500, detail="Internal error creating domain")
    return _to_response(domain)


@router.get("/", response_model=List[DomainResponse])
async def list_domains(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[DomainResponse]:
    service = DomainService(db)
    domains = service.list_domains(tenant_id=user.tenant_id)
    return [_to_response(d) for d in domains]


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DomainResponse:
    service = DomainService(db)
    domain = service.get_domain(domain_id=domain_id, tenant_id=user.tenant_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return _to_response(domain)


@router.patch("/{domain_id}", response_model=DomainResponse)
async def set_primary(
    domain_id: UUID,
    body: DomainSetPrimary,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DomainResponse:
    if not body.is_primary:
        raise HTTPException(status_code=400, detail="Use is_primary=true to set a domain as primary")
    service = DomainService(db)
    try:
        domain = service.set_primary(domain_id=domain_id, tenant_id=user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _to_response(domain)


@router.delete("/{domain_id}", status_code=204)
async def delete_domain(
    domain_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    service = DomainService(db)
    try:
        service.delete_domain(domain_id=domain_id, tenant_id=user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{domain_id}/verify", response_model=DomainResponse)
async def verify_domain(
    domain_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DomainResponse:
    service = DomainService(db)
    try:
        domain = service.verify_domain(domain_id=domain_id, tenant_id=user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("domain_verify_error", error=str(e), domain_id=str(domain_id))
        raise HTTPException(status_code=502, detail="Cloudflare verification failed")
    return _to_response(domain)


@router.get("/{domain_id}/instructions", response_model=DomainInstructionsResponse)
async def get_domain_instructions(
    domain_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DomainInstructionsResponse:
    """Return DNS setup instructions for a custom domain."""
    service = DomainService(db)
    domain = service.get_domain_instructions(domain_id=domain_id, tenant_id=user.tenant_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    cname_record: DnsRecord | None = None
    txt_record: DnsRecord | None = None

    if domain.verification_cname_target:
        cname_record = DnsRecord(
            type="CNAME",
            name="@",
            target=domain.verification_cname_target,
        )

    if domain.verification_txt_name and domain.verification_txt_value:
        txt_record = DnsRecord(
            type="TXT",
            name=domain.verification_txt_name,
            value=domain.verification_txt_value,
        )

    return DomainInstructionsResponse(
        hostname=domain.hostname,
        domain_type=domain.domain_type,
        status=domain.status,
        cname_record=cname_record,
        txt_record=txt_record,
    )
