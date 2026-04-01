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
        self.headers = {
            "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        }

    def create_custom_hostname(self, hostname: str) -> dict:
        """Create a Custom Hostname in CF for SaaS. Returns verification records."""
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
        url = f"{self.BASE_URL}/zones/{self.zone_id}/custom_hostnames/{cf_hostname_id}"
        with httpx.Client() as client:
            response = client.delete(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()

    def get_hostname_status(self, cf_hostname_id: str) -> dict:
        """Get current CF Custom Hostname status (ssl + ownership verification)."""
        url = f"{self.BASE_URL}/zones/{self.zone_id}/custom_hostnames/{cf_hostname_id}"
        with httpx.Client() as client:
            response = client.get(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
            return response.json().get("result", {})

    def put_kv(self, key: str, value: dict) -> None:
        """Write hostname -> tenant mapping to Workers KV."""
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
        url = (
            f"{self.BASE_URL}/accounts/{self.account_id}"
            f"/storage/kv/namespaces/{self.kv_namespace_id}/values/{key}"
        )
        with httpx.Client() as client:
            response = client.delete(url, headers=self.headers, timeout=30.0)
            response.raise_for_status()
