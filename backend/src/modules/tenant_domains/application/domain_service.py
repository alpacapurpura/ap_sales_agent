import socket
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy.orm import Session

from src.modules.tenant_domains.domain.domain_entity import (
    DomainStatus,
    DomainType,
    TenantDomain,
)
from src.modules.tenant_domains.infrastructure.cloudflare_client import CloudflareClient
from src.modules.tenant_domains.infrastructure.domain_repository_impl import (
    DomainRepositoryImpl,
)

logger = structlog.get_logger()

# Known provider IP ranges — extend as new providers are discovered
_KNOWN_PROVIDERS: dict[str, dict[str, str]] = {
    "23.227.38.32": {"provider": "Shopify", "suggestion_prefix": "go"},
    "23.227.38.33": {"provider": "Shopify", "suggestion_prefix": "go"},
    "23.227.38.34": {"provider": "Shopify", "suggestion_prefix": "go"},
}


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
            self.cf.put_kv(
                hostname,
                {
                    "tenant_id": str(tenant_id),
                    "slug": slug,
                    "type": "platform",
                },
            )
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
            cname_target = cf_result.get("ownership_verification_http", {}).get(
                "http_url"
            )
            if cname_target:
                domain.verification_cname_target = cname_target
        except Exception as e:
            logger.error(
                "cf_custom_hostname_create_failed", hostname=hostname, error=str(e)
            )
            domain.status = DomainStatus.FAILED
        return self.repo.create(domain)

    def verify_domain(self, domain_id: UUID, tenant_id: UUID) -> TenantDomain:
        """Trigger a verification check with Cloudflare."""
        domain = self.repo.get_by_id(domain_id, tenant_id)
        if not domain:
            msg = "Domain not found"
            raise ValueError(msg)
        if not domain.cloudflare_hostname_id:
            msg = "No CF hostname ID — cannot verify"
            raise ValueError(msg)

        cf_status = self.cf.get_hostname_status(domain.cloudflare_hostname_id)
        ssl = cf_status.get("ssl", {})
        if ssl.get("status") == "active":
            domain.status = DomainStatus.ACTIVE
            domain.ssl_status = "active"
            domain.verified_at = datetime.now(UTC)
            try:
                self.cf.put_kv(
                    domain.hostname,
                    {
                        "tenant_id": str(tenant_id),
                        "type": "custom",
                    },
                )
            except Exception as e:
                logger.warning(
                    "cf_kv_sync_failed", hostname=domain.hostname, error=str(e)
                )
        else:
            domain.status = DomainStatus.VERIFYING
            domain.ssl_status = ssl.get("status")

        return self.repo.update(domain)

    def delete_domain(self, domain_id: UUID, tenant_id: UUID) -> None:
        """Soft delete domain and clean up CF resources."""
        domain = self.repo.get_by_id(domain_id, tenant_id)
        if not domain:
            msg = "Domain not found"
            raise ValueError(msg)
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

    def list_domains(self, tenant_id: UUID) -> list[TenantDomain]:
        return self.repo.list_by_tenant(tenant_id)

    def get_domain(self, domain_id: UUID, tenant_id: UUID) -> TenantDomain | None:
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
            msg = "Domain not found"
            raise ValueError(msg)
        domain.is_primary = True
        return self.repo.update(domain)

    @staticmethod
    def _extract_root_domain(hostname: str) -> str:
        """Extract root domain: 'go.visionarias.lat' -> 'visionarias.lat'"""
        parts = hostname.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return hostname

    def detect_domain_conflict(self, hostname: str) -> dict | None:
        """
        Check if the root domain's A record points to a known provider (e.g. Shopify).
        Returns conflict info with a subdomain suggestion, or None if clean.
        """
        root_domain = self._extract_root_domain(hostname)
        try:
            ip = socket.gethostbyname(root_domain)
            provider_info = _KNOWN_PROVIDERS.get(ip)
            if provider_info:
                suggestion = f"{provider_info['suggestion_prefix']}.{root_domain}"
                logger.info(
                    "domain_conflict_detected",
                    hostname=hostname,
                    root_domain=root_domain,
                    provider=provider_info["provider"],
                    detected_ip=ip,
                )
                return {
                    "provider": provider_info["provider"],
                    "detected_ip": ip,
                    "suggestion": suggestion,
                    "message": (
                        f"El dominio raíz {root_domain!r} apunta a {provider_info['provider']}. "
                        f"Te recomendamos usar un subdominio: {suggestion!r}"
                    ),
                }
        except (socket.gaierror, OSError):
            # DNS resolution failure — domain not resolvable, no conflict
            pass
        return None

    def get_domain_instructions(
        self, domain_id: UUID, tenant_id: UUID
    ) -> TenantDomain | None:
        """Return the domain entity so the API layer can build DNS setup instructions."""
        return self.repo.get_by_id(domain_id, tenant_id)
