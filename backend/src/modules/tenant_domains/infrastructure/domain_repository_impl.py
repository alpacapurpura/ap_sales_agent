from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.modules.tenant_domains.domain.domain_entity import TenantDomain, DomainStatus, DomainType
from src.modules.tenant_domains.domain.domain_repository import DomainRepository
from src.modules.tenant_domains.infrastructure.models.tenant_domain_model import TenantDomainModel

logger = structlog.get_logger()


class DomainRepositoryImpl(DomainRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: TenantDomainModel) -> TenantDomain:
        return TenantDomain(
            id=model.id,
            tenant_id=model.tenant_id,
            hostname=model.hostname,
            domain_type=DomainType(model.domain_type),
            status=DomainStatus(model.status),
            is_primary=model.is_primary,
            cloudflare_hostname_id=model.cloudflare_hostname_id,
            ssl_status=model.ssl_status,
            verification_method=model.verification_method,
            verification_cname_target=model.verification_cname_target,
            verification_txt_name=model.verification_txt_name,
            verification_txt_value=model.verification_txt_value,
            verified_at=model.verified_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def create(self, domain: TenantDomain) -> TenantDomain:
        model = TenantDomainModel(
            id=domain.id,
            tenant_id=domain.tenant_id,
            hostname=domain.hostname,
            domain_type=domain.domain_type.value,
            status=domain.status.value,
            is_primary=domain.is_primary,
            cloudflare_hostname_id=domain.cloudflare_hostname_id,
            ssl_status=domain.ssl_status,
            verification_method=domain.verification_method,
            verification_cname_target=domain.verification_cname_target,
            verification_txt_name=domain.verification_txt_name,
            verification_txt_value=domain.verification_txt_value,
            verified_at=domain.verified_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        logger.info("domain_created", domain_id=str(model.id), tenant_id=str(model.tenant_id), hostname=model.hostname)
        return self._to_domain(model)

    def get_by_id(self, domain_id: UUID, tenant_id: UUID) -> Optional[TenantDomain]:
        stmt = select(TenantDomainModel).where(
            TenantDomainModel.id == domain_id,
            TenantDomainModel.tenant_id == tenant_id,
            TenantDomainModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def get_by_hostname(self, hostname: str) -> Optional[TenantDomain]:
        stmt = select(TenantDomainModel).where(
            TenantDomainModel.hostname == hostname,
            TenantDomainModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_tenant(self, tenant_id: UUID) -> List[TenantDomain]:
        stmt = select(TenantDomainModel).where(
            TenantDomainModel.tenant_id == tenant_id,
            TenantDomainModel.deleted_at.is_(None),
        ).order_by(TenantDomainModel.created_at)
        result = self.db.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    def update(self, domain: TenantDomain) -> TenantDomain:
        stmt = select(TenantDomainModel).where(
            TenantDomainModel.id == domain.id,
            TenantDomainModel.tenant_id == domain.tenant_id,
            TenantDomainModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Domain {domain.id} not found for tenant {domain.tenant_id}")
        model.status = domain.status.value
        model.is_primary = domain.is_primary
        model.cloudflare_hostname_id = domain.cloudflare_hostname_id
        model.ssl_status = domain.ssl_status
        model.verification_method = domain.verification_method
        model.verification_cname_target = domain.verification_cname_target
        model.verification_txt_name = domain.verification_txt_name
        model.verification_txt_value = domain.verification_txt_value
        model.verified_at = domain.verified_at
        self.db.commit()
        self.db.refresh(model)
        logger.info("domain_updated", domain_id=str(model.id), status=model.status)
        return self._to_domain(model)

    def soft_delete(self, domain_id: UUID, tenant_id: UUID) -> None:
        stmt = select(TenantDomainModel).where(
            TenantDomainModel.id == domain_id,
            TenantDomainModel.tenant_id == tenant_id,
            TenantDomainModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return
        model.deleted_at = func.now()
        self.db.commit()
        logger.info("domain_soft_deleted", domain_id=str(domain_id), tenant_id=str(tenant_id))
