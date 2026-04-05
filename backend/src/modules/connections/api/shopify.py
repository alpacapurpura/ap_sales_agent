import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.marketing_connectors.shopify import (
    ShopifyConnector,
)
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger()
router = APIRouter()
public_router = APIRouter()


class ShopifyAuthUrlRequest(BaseModel):
    shop_url: str


class ShopifyExchangeRequest(BaseModel):
    code: str
    shop: str
    hmac: str
    state: str | None = None
    host: str | None = None
    timestamp: str | None = None


class ShopifyStatusResponse(BaseModel):
    is_connected: bool
    shop_url: str | None = None
    shop_info: dict[str, Any] | None = None


class ConnectionResponse(BaseModel):
    status: str
    message: str
    details: dict[str, Any] | None = None


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _resolve_tenant_id(
    repo: ChannelConnectionRepository,
    shop: str,
    state: str | None,
) -> uuid.UUID:
    if state:
        try:
            return uuid.UUID(state)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

    connection = repo.get_active_shopify_by_shop(shop)
    if not connection:
        raise HTTPException(status_code=400, detail="Tenant resolution failed for shop")

    return connection.tenant_id


@router.get("/status", response_model=ShopifyStatusResponse)
async def get_shopify_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.SHOPIFY)

    if not connection:
        return ShopifyStatusResponse(is_connected=False)

    return ShopifyStatusResponse(
        is_connected=True,
        shop_url=connection.config.get("shop_url"),
        shop_info=connection.config.get("shop_info"),
    )


@router.post("/generate-auth-url")
async def generate_auth_url(
    request: ShopifyAuthUrlRequest,
    user: User = Depends(get_current_user),
):
    state = str(user.tenant_id)

    base_url = settings.DASHBOARD_DOMAIN.rstrip("/")
    # Point to the Next.js frontend API route that handles the callback and proxies to the backend
    redirect_uri = f"{base_url}/api/auth/shopify/callback"

    # Ensure URL is HTTPS
    if redirect_uri.startswith("http://"):
        redirect_uri = redirect_uri.replace("http://", "https://")

    auth_url = ShopifyConnector.get_auth_url(
        shop_domain=request.shop_url,
        state=state,
        redirect_uri=redirect_uri,
    )

    return {"auth_url": auth_url}


@public_router.post("/auth/exchange", response_model=ConnectionResponse)
async def exchange_shopify_token(
    request: ShopifyExchangeRequest,
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    params = request.model_dump(exclude_none=True)

    if not ShopifyConnector.verify_hmac(params):
        raise HTTPException(status_code=400, detail="Invalid HMAC signature")

    tenant_id = _resolve_tenant_id(
        repo=repo,
        shop=request.shop,
        state=request.state,
    )

    access_token, error = await ShopifyConnector.exchange_token(
        request.shop, request.code
    )
    if error:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {error}")

    is_valid, shop_details = await ShopifyConnector.verify_connection(
        request.shop, access_token
    )
    if not is_valid:
        raise HTTPException(
            status_code=400, detail="Failed to verify connection with Shopify"
        )

    repo.upsert(
        tenant_id=tenant_id,
        channel_type=ChannelType.SHOPIFY,
        credentials={"access_token": access_token},
        config={"shop_url": f"https://{request.shop}", "shop_info": shop_details},
    )

    return ConnectionResponse(
        status="connected",
        message="Shopify connected successfully",
        details=shop_details,
    )


@public_router.get("/auth/callback")
async def auth_callback(
    request: Request,
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    params = dict(request.query_params)

    if not ShopifyConnector.verify_hmac(params):
        raise HTTPException(status_code=400, detail="Invalid HMAC signature")

    shop = params.get("shop")
    code = params.get("code")
    state = params.get("state")

    if not shop or not code:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    tenant_id = _resolve_tenant_id(
        repo=repo,
        shop=shop,
        state=state,
    )

    access_token, error = await ShopifyConnector.exchange_token(shop, code)
    if error:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {error}")

    is_valid, shop_details = await ShopifyConnector.verify_connection(
        shop, access_token
    )
    if not is_valid:
        raise HTTPException(
            status_code=400, detail="Failed to verify connection with Shopify"
        )

    repo.upsert(
        tenant_id=tenant_id,
        channel_type=ChannelType.SHOPIFY,
        credentials={"access_token": access_token},
        config={"shop_url": f"https://{shop}", "shop_info": shop_details},
    )

    dashboard_url = settings.DASHBOARD_DOMAIN
    if not dashboard_url:
        raise HTTPException(
            status_code=500, detail="DASHBOARD_DOMAIN not configured on server"
        )
    return RedirectResponse(
        url=f"{dashboard_url}/growth-studio/connections?status=success&channel=shopify"
    )


@router.post("/quick-connect", response_model=ConnectionResponse)
async def quick_connect_shopify(
    request: ShopifyAuthUrlRequest,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """
    Connect to Shopify using Client Credentials Grant (no browser redirect).
    Only works for stores in the same Shopify organization as the app.
    """
    shop_url = (
        request.shop_url.replace("https://", "").replace("http://", "").strip("/")
    )
    if not shop_url.endswith("myshopify.com") and "." not in shop_url:
        shop_url = f"{shop_url}.myshopify.com"

    access_token, error = await ShopifyConnector.client_credentials_token(shop_url)
    if error:
        raise HTTPException(
            status_code=400, detail=f"Client credentials failed: {error}"
        )

    is_valid, shop_details = await ShopifyConnector.verify_connection(
        shop_url, access_token
    )
    if not is_valid:
        raise HTTPException(
            status_code=400, detail="Failed to verify connection with Shopify"
        )

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.SHOPIFY,
        credentials={"access_token": access_token},
        config={"shop_url": f"https://{shop_url}", "shop_info": shop_details},
    )

    return ConnectionResponse(
        status="connected",
        message="Shopify connected via client credentials",
        details=shop_details,
    )


@router.post("/disconnect", response_model=ConnectionResponse)
async def disconnect_shopify(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.SHOPIFY)

    if not connection:
        raise HTTPException(status_code=404, detail="No Shopify connection found")

    repo.deactivate(connection)

    return ConnectionResponse(
        status="disconnected",
        message="Shopify disconnected successfully",
    )


@router.post("/test", response_model=ConnectionResponse)
async def test_shopify_connection(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_active(user.tenant_id, ChannelType.SHOPIFY)

    if not connection:
        raise HTTPException(
            status_code=404, detail="No active Shopify connection found"
        )

    access_token = connection.credentials.get("access_token")
    shop_url = connection.config.get("shop_url")

    if not access_token or not shop_url:
        raise HTTPException(status_code=400, detail="Incomplete connection data")

    is_valid, result = await ShopifyConnector.verify_connection(
        shop_url=shop_url,
        access_token=access_token,
    )

    if is_valid:
        repo.update_config(connection, {"shop_info": result})
        return ConnectionResponse(
            status="active", message="Connection is valid", details=result
        )

    return ConnectionResponse(
        status="error", message="Connection test failed", details=result
    )
