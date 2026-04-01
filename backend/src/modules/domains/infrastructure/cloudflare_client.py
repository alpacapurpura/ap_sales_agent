"""
Cloudflare API client for Custom Domains feature.
Handles: Custom Hostnames API + Workers KV API.
"""
import json

import httpx
import structlog

from src.core.config import settings

logger = structlog.get_logger()


class CloudflareClient:
    BASE_URL = "https://api.cloudflare.com/client/v4"

    def __init__(self) -> None:
        self.zone_id = settings.CLOUDFLARE_ZONE_ID
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.kv_namespace_id = settings.CLOUDFLARE_KV_NAMESPACE_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.is_configured = bool(self.zone_id and self.api_token and self.kv_namespace_id)
        if not self.is_configured:
            logger.warning(
                "cloudflare_not_configured",
                detail="CF operations will be no-ops in this environment",
            )
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def create_custom_hostname(self, hostname: str) -> dict:
        """Create a Custom Hostname in CF for SaaS. Returns verification records."""
        if not self.is_configured:
            logger.info("cf_skip_not_configured", operation="create_custom_hostname", hostname=hostname)
            return {}
        url = f"{self.BASE_URL}/zones/{self.zone_id}/custom_hostnames"
        payload = {
            "hostname": hostname,
            "ssl": {"method": "http", "type": "dv"},
        }
        with httpx.Client() as client:
            response = client.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json().get("result", {})

    def delete_custom_hostname(self, cf_hostname_id: str) -> None:
        """Delete a CF Custom Hostname."""
        if not self.is_configured:
            logger.info("cf_skip_not_configured", operation="delete_custom_hostname", cf_hostname_id=cf_hostname_id)
            return
        url = f"{self.BASE_URL}/zones/{self.zone_id}/custom_hostnames/{cf_hostname_id}"
        with httpx.Client() as client:
            response = client.delete(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()

    def get_hostname_status(self, cf_hostname_id: str) -> dict:
        """Get current CF Custom Hostname status (ssl + ownership verification)."""
        if not self.is_configured:
            logger.info("cf_skip_not_configured", operation="get_hostname_status", cf_hostname_id=cf_hostname_id)
            return {}
        url = f"{self.BASE_URL}/zones/{self.zone_id}/custom_hostnames/{cf_hostname_id}"
        with httpx.Client() as client:
            response = client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json().get("result", {})

    def put_kv(self, key: str, value: dict) -> None:
        """Write hostname -> tenant mapping to Workers KV."""
        if not self.is_configured:
            logger.info("cf_skip_not_configured", operation="put_kv", key=key)
            return
        url = (
            f"{self.BASE_URL}/accounts/{self.account_id}"
            f"/storage/kv/namespaces/{self.kv_namespace_id}/values/{key}"
        )
        with httpx.Client() as client:
            response = client.put(
                url,
                content=json.dumps(value),
                headers={**self.headers, "Content-Type": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()

    def delete_kv(self, key: str) -> None:
        """Remove hostname mapping from Workers KV."""
        if not self.is_configured:
            logger.info("cf_skip_not_configured", operation="delete_kv", key=key)
            return
        url = (
            f"{self.BASE_URL}/accounts/{self.account_id}"
            f"/storage/kv/namespaces/{self.kv_namespace_id}/values/{key}"
        )
        with httpx.Client() as client:
            response = client.delete(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
