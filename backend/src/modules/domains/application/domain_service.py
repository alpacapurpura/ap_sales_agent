from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy.orm import Session

from src.modules.domains.domain.domain_entity import TenantDomain, DomainStatus, DomainType
from src.modules.domains.infrastructure.cloudflare_client import CloudflareClient
from src.modules.domains.infrastructure.domain_repository_impl import DomainRepositoryImpl

logger = structlog.get_logger()


class DomainService:
    def __init__(self, db: Session) -> None:
        self.repo = DomainRepositoryImpl(db)
        self.cf = CloudflareClient()

    def create_platform_domain(self, tenant_id: UUID, slug: str) -> TenantDomain:
        """Create {slug}.nicolify.com platform subdomain and sync to Workers KV."""
        hostname = f"{slug}.nicolify.com"
        domain = TenantDomain(
            id=uuid4(),
            tenant_id=tenant_id,
            hostname=hostname,
            domain_type=DomainType.PLATFORM,
            status=DomainStatus.ACTIVE,
            is_primary=False,
        )
        saved = self.repo.create(domain)
        try:
            self.cf.put_kv(hostname, {
                "tenant_id": str(tenant_id),
                "slug": slug,
                "type": "platform",
            })
        except Exception as e:
            logger.warning("cf_kv_sync_failed", hostname=hostname, error=str(e))
        return saved

    def create_custom_domain(self, tenant_id: UUID, hostname: str) -> TenantDomain:
        """Register custom domain with CF Custom Hostnames and save verification records."""
        domain = TenantDomain(
            id=uuid4(),
            tenant_id=tenant_id,
            hostname=hostname,
            domain_type=DomainType.CUSTOM,
            status=DomainStatus.PENDING_VERIFICATION,
        )
        try:
            cf_result = self.cf.create_custom_hostname(hostname)
            domain.cloudflare_hostname_id = cf_result.get("id")
            domain.ssl_status = cf_result.get("ssl", {}).get("status")
            ownership = cf_result.get("ownership_verification", {})
            domain.verification_method = ownership.get("type")
            if ownership.get("type") == "txt":
                domain.verification_txt_name = ownership.get("name")
                domain.verification_txt_value = ownership.get("value")
            cname_target = cf_result.get("ownership_verification_http", {}).get("http_url")
            if cname_target:
                domain.verification_cname_target = cname_target
        except Exception as e:
            logger.error("cf_custom_hostname_create_failed", hostname=hostname, error=str(e))
            domain.status = DomainStatus.FAILED
        return self.repo.create(domain)

    def verify_domain(self, domain_id: UUID, tenant_id: UUID) -> TenantDomain:
        """Trigger a verification check with Cloudflare."""
        domain = self.repo.get_by_id(domain_id, tenant_id)
        if not domain:
            raise ValueError("Domain not found")
        if not domain.cloudflare_hostname_id:
            raise ValueError("No CF hostname ID — cannot verify")

        cf_status = self.cf.get_hostname_status(domain.cloudflare_hostname_id)
        ssl = cf_status.get("ssl", {})
        if ssl.get("status") == "active":
            domain.status = DomainStatus.ACTIVE
            domain.ssl_status = "active"
            domain.verified_at = datetime.now(timezone.utc)
            try:
                self.cf.put_kv(domain.hostname, {
                    "tenant_id": str(tenant_id),
                    "type": "custom",
                })
            except Exception as e:
                logger.warning("cf_kv_sync_failed", hostname=domain.hostname, error=str(e))
        else:
            domain.status = DomainStatus.VERIFYING
            domain.ssl_status = ssl.get("status")

        return self.repo.update(domain)

    def delete_domain(self, domain_id: UUID, tenant_id: UUID) -> None:
        """Soft delete domain and clean up CF resources."""
        domain = self.repo.get_by_id(domain_id, tenant_id)
        if not domain:
            raise ValueError("Domain not found")
        if domain.cloudflare_hostname_id:
            try:
                self.cf.delete_custom_hostname(domain.cloudflare_hostname_id)
            except Exception as e:
                logger.warning("cf_delete_failed", error=str(e))
        try:
            self.cf.delete_kv(domain.hostname)
        except Exception as e:
            logger.warning("cf_kv_delete_failed", error=str(e))
        self.repo.soft_delete(domain_id, tenant_id)

    def list_domains(self, tenant_id: UUID) -> List[TenantDomain]:
        return self.repo.list_by_tenant(tenant_id)

    def get_domain(self, domain_id: UUID, tenant_id: UUID) -> Optional[TenantDomain]:
        return self.repo.get_by_id(domain_id, tenant_id)

    def set_primary(self, domain_id: UUID, tenant_id: UUID) -> TenantDomain:
        """Set a domain as primary (unsets previous primary for tenant)."""
        current_domains = self.repo.list_by_tenant(tenant_id)
        for d in current_domains:
            if d.is_primary and d.id != domain_id:
                d.is_primary = False
                self.repo.update(d)
        domain = self.repo.get_by_id(domain_id, tenant_id)
        if not domain:
            raise ValueError("Domain not found")
        domain.is_primary = True
        return self.repo.update(domain)
