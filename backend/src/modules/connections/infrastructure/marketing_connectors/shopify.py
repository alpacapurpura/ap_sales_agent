import httpx
import structlog
from typing import Dict, Any, Tuple, List, Optional
from fastapi import HTTPException
from src.modules.connections.infrastructure.marketing_connectors.base import BaseConnector
from src.core.config import settings
import hmac
import hashlib
import urllib.parse

logger = structlog.get_logger()

class ShopifyConnector(BaseConnector):
    """
    Shopify Connector for verifying credentials and interacting with Shopify Admin API.
    """
    
    API_VERSION = "2024-01"
    SCOPES = "read_customers,write_customers,read_orders,write_orders,read_products" # Default scopes

    @staticmethod
    def get_auth_url(shop_domain: str, state: str, redirect_uri: str) -> str:
        """
        Generates the Shopify OAuth authorization URL.
        """
        # Clean up shop URL
        shop_domain = shop_domain.replace("https://", "").replace("http://", "").strip("/")
        if not shop_domain.endswith("myshopify.com") and "." not in shop_domain:
            shop_domain = f"{shop_domain}.myshopify.com"
            
        params = {
            "client_id": settings.SHOPIFY_API_KEY,
            "scope": ShopifyConnector.SCOPES,
            "redirect_uri": redirect_uri,
            "state": state
        }
        query_string = urllib.parse.urlencode(params)
        return f"https://{shop_domain}/admin/oauth/authorize?{query_string}"

    @staticmethod
    def verify_hmac(query_params: dict) -> bool:
        """
        Verifies the HMAC signature of the request from Shopify.
        """
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
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(hmac_param, signature)

    @staticmethod
    async def exchange_token(shop_domain: str, code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Exchanges the authorization code for a permanent access token.
        Returns: (access_token, error_message)
        """
        url = f"https://{shop_domain}/admin/oauth/access_token"
        payload = {
            "client_id": settings.SHOPIFY_API_KEY,
            "client_secret": settings.SHOPIFY_API_SECRET,
            "code": code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token"), None
                else:
                    logger.error("shopify_token_exchange_failed", status=response.status_code, body=response.text)
                    return None, f"Failed to exchange token: {response.text}"
        except Exception as e:
            logger.error("shopify_token_exchange_error", error=str(e))
            return None, str(e)

    def sync_contacts(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Sync contacts from Shopify (Customers).
        Placeholder implementation.
        """
        logger.info("shopify_sync_contacts_placeholder", tenant_id=tenant_id)
        return []

    def sync_events(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Sync events from Shopify (Orders).
        Placeholder implementation.
        """
        logger.info("shopify_sync_events_placeholder", tenant_id=tenant_id)
        return []

    @staticmethod
    async def verify_connection(shop_url: str, access_token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verifies Shopify connection by fetching shop details.
        
        Args:
            shop_url: The myshopify.com URL (e.g., "mystore.myshopify.com")
            access_token: The Admin API access token
            
        Returns:
            Tuple[bool, Dict]: (is_valid, shop_details_or_error)
        """
        # Clean up shop URL
        shop_domain = shop_url.replace("https://", "").replace("http://", "").strip("/")
        if not shop_domain.endswith("myshopify.com"):
            # Append if missing, though user should provide full domain usually
            if "." not in shop_domain:
                shop_domain = f"{shop_domain}.myshopify.com"
        
        url = f"https://{shop_domain}/admin/api/{ShopifyConnector.API_VERSION}/shop.json"
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
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
                        "plan_name": shop.get("plan_name")
                    }
                elif response.status_code == 401:
                    logger.warning("shopify_auth_failed", shop=shop_domain, status=401)
                    return False, {"error": "Invalid access token"}
                elif response.status_code == 404:
                    logger.warning("shopify_shop_not_found", shop=shop_domain, status=404)
                    return False, {"error": "Shop not found"}
                else:
                    logger.error("shopify_connection_error", shop=shop_domain, status=response.status_code, body=response.text)
                    return False, {"error": f"Shopify API error: {response.status_code}"}
                    
        except httpx.RequestError as e:
            logger.error("shopify_network_error", error=str(e))
            return False, {"error": f"Network error: {str(e)}"}
        except Exception as e:
            logger.error("shopify_unexpected_error", error=str(e))
            return False, {"error": f"Unexpected error: {str(e)}"}
