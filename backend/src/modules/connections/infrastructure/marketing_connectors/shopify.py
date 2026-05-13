"""Shopify marketing connector."""

import hashlib
import hmac
import urllib.parse
from typing import Any

import httpx
import structlog
from luana_core_connections.infrastructure.marketing_connectors.base import (
    BaseConnector,
)
from luana_core_platform.core.config import settings

logger = structlog.get_logger()


class ShopifyConnector(BaseConnector):
    """Shopify Connector for verifying credentials and interacting with Shopify Admin API."""

    API_VERSION = "2026-01"
    SCOPES = (  # Default scopes
        "write_customers,write_orders,read_analytics,read_customer_events,"
        "read_cart_transforms,read_all_cart_transforms,read_channels,read_checkouts,"
        "read_companies,read_custom_pixels,read_customers,read_customer_data_erasure,"
        "read_customer_merge,read_price_rules,read_discounts,"
        "read_discounts_allocator_functions,read_discovery,read_draft_orders,"
        "read_fulfillments,read_gift_card_transactions,read_gift_cards,read_inventory,"
        "read_inventory_shipments,read_inventory_shipments_received_items,read_locales,"
        "read_locations,read_marketing_integrated_campaigns,read_marketing_events,"
        "read_markets,read_markets_home,read_merchant_managed_fulfillment_orders,"
        "read_metaobject_definitions,read_metaobjects,read_online_store_navigation,"
        "read_online_store_pages,read_order_edits,read_orders,"
        "read_packing_slip_templates,read_payment_terms,read_payment_customizations,"
        "read_product_feeds,read_product_listings,read_products,read_publications,"
        "read_purchase_options,read_reports,read_resource_feedbacks,read_returns,"
        "read_script_tags,read_shipping,read_shopify_payments_payouts,"
        "read_shopify_payments_disputes,read_content,"
        "read_store_credit_account_transactions,read_third_party_fulfillment_orders,"
        "read_translations,read_pixels"
    )

    @staticmethod
    def get_auth_url(shop_domain: str, state: str, redirect_uri: str) -> str:
        """Generate the Shopify OAuth authorization URL.

        Scopes must be explicit for Custom Distribution apps not deployed via CLI/TOML.
        """
        # Clean up shop URL
        shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")
        if not shop_domain.endswith("myshopify.com") and "." not in shop_domain:
            shop_domain = f"{shop_domain}.myshopify.com"

        params = {
            "client_id": settings.SHOPIFY_API_KEY,
            "scope": ShopifyConnector.SCOPES,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        query_string = urllib.parse.urlencode(params)
        return f"https://{shop_domain}/admin/oauth/authorize?{query_string}"

    @staticmethod
    def verify_hmac(query_params: dict) -> bool:
        """Verify the HMAC signature of the request from Shopify."""
        if "hmac" not in query_params:
            return False

        hmac_param = query_params["hmac"]
        # Remove hmac from params to calculate signature
        params = query_params.copy()
        del params["hmac"]

        # Sort keys lexicographically and join key=value
        sorted_params = sorted(params.items())
        message = "&".join([f"{key}={value}" for key, value in sorted_params])

        secret = settings.SHOPIFY_API_SECRET.encode("utf-8")
        signature = hmac.new(
            secret,
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(hmac_param, signature)

    @staticmethod
    async def exchange_token(
        shop_domain: str,
        code: str,
    ) -> tuple[str | None, str | None]:
        """Exchanges the authorization code for a permanent access token.

        Returns: (access_token, error_message)
        """
        url = f"https://{shop_domain}/admin/oauth/access_token"
        payload = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token"), None
                logger.error(
                    "shopify_token_exchange_failed",
                    status=response.status_code,
                    body=response.text,
                )
                return None, f"Failed to exchange token: {response.text}"
        except Exception as e:
            logger.exception("shopify_token_exchange_error", error=str(e))
            return None, str(e)

    @staticmethod
    async def client_credentials_token(
        shop_domain: str,
    ) -> tuple[str | None, str | None]:
        """Acquires an access token via OAuth 2.0 Client Credentials Grant.

        Only works for apps installed on stores owned by the same organization.
        Token expires in ~24h and must be refreshed.
        Returns: (access_token, error_message)
        """
        shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")
        if not shop_domain.endswith("myshopify.com") and "." not in shop_domain:
            shop_domain = f"{shop_domain}.myshopify.com"

        url = f"https://{shop_domain}/admin/oauth/access_token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token"), None
                logger.error(
                    "shopify_client_credentials_failed",
                    status=response.status_code,
                    body=response.text,
                )
                return None, f"Client credentials failed: {response.text}"
        except Exception as e:
            logger.exception("shopify_client_credentials_error", error=str(e))
            return None, str(e)

    def sync_contacts(self, tenant_id: str) -> list[dict[str, Any]]:
        """Sync contacts from Shopify (Customers).

        Placeholder implementation.
        """
        logger.info("shopify_sync_contacts_placeholder", tenant_id=tenant_id)
        return []

    def sync_events(self, tenant_id: str) -> list[dict[str, Any]]:
        """Sync events from Shopify (Orders).

        Placeholder implementation.
        """
        logger.info("shopify_sync_events_placeholder", tenant_id=tenant_id)
        return []

    @staticmethod
    async def verify_connection(
        shop_url: str,
        access_token: str,
    ) -> tuple[bool, dict[str, Any]]:
        """Verify Shopify connection by fetching shop details.

        Args:
            shop_url: The myshopify.com URL (e.g., "mystore.myshopify.com")
            access_token: The Admin API access token

        Returns:
            Tuple[bool, Dict]: (is_valid, shop_details_or_error)

        """
        # Clean up shop URL
        shop_domain = shop_url.replace("https://", "").replace("http://", "").strip("/")
        if not shop_domain.endswith("myshopify.com"):  # noqa: SIM102
            # Append if missing, though user should provide full domain usually
            if "." not in shop_domain:
                shop_domain = f"{shop_domain}.myshopify.com"

        url = f"https://{shop_domain}/admin/api/{ShopifyConnector.API_VERSION}/shop.json"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()
                    shop = data.get("shop", {})
                    return True, {
                        "id": shop.get("id"),
                        "name": shop.get("name"),
                        "email": shop.get("email"),
                        "domain": shop.get("domain"),
                        "currency": shop.get("currency"),
                        "shop_owner": shop.get("shop_owner"),
                        "plan_name": shop.get("plan_name"),
                    }
                if response.status_code == 401:
                    logger.warning("shopify_auth_failed", shop=shop_domain, status=401)
                    return False, {"error": "Invalid access token"}
                if response.status_code == 404:
                    logger.warning(
                        "shopify_shop_not_found",
                        shop=shop_domain,
                        status=404,
                    )
                    return False, {"error": "Shop not found"}
                logger.error(
                    "shopify_connection_error",
                    shop=shop_domain,
                    status=response.status_code,
                    body=response.text,
                )
                return False, {"error": f"Shopify API error: {response.status_code}"}

        except httpx.RequestError as e:
            logger.exception("shopify_network_error", error=str(e))
            return False, {"error": f"Network error: {e!s}"}
        except Exception as e:
            logger.exception("shopify_unexpected_error", error=str(e))
            return False, {"error": f"Unexpected error: {e!s}"}
