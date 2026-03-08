from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Dict, Any, Optional
from pydantic import BaseModel
import uuid

from src.core.database import get_db
from src.core.config import settings
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.connections.domain.enums import ChannelType
from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel
from src.modules.connections.infrastructure.marketing_connectors.shopify import ShopifyConnector
import structlog

logger = structlog.get_logger()
router = APIRouter()
public_router = APIRouter()

# --- Pydantic Models ---

class ShopifyAuthUrlRequest(BaseModel):
    shop_url: str

class ShopifyExchangeRequest(BaseModel):
    code: str
    shop: str
    hmac: str
    state: str
    host: Optional[str] = None
    timestamp: Optional[str] = None

class ShopifyStatusResponse(BaseModel):
    is_connected: bool
    shop_url: Optional[str] = None
    shop_info: Optional[Dict[str, Any]] = None

class ConnectionResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

# --- Endpoints ---

@router.get("/status", response_model=ShopifyStatusResponse)
async def get_shopify_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if Shopify is connected for the current tenant.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.SHOPIFY.value,
        ChannelConnectionModel.is_active.is_(True)
    ).first()

    if not connection:
        return ShopifyStatusResponse(is_connected=False)

    return ShopifyStatusResponse(
        is_connected=True,
        shop_url=connection.config.get("shop_url"),
        shop_info=connection.config.get("shop_info")
    )

@router.post("/generate-auth-url")
async def generate_auth_url(
    request: ShopifyAuthUrlRequest,
    user: User = Depends(get_current_user)
):
    """
    Generate Shopify OAuth authorization URL.
    """
    # Use tenant_id as state for simplicity (in prod use signed state/nonce)
    state = str(user.tenant_id)
    
    # Construct redirect URI
    # Use DASHBOARD_DOMAIN for frontend callback handling
    base_url = settings.DASHBOARD_DOMAIN.rstrip("/")
    redirect_uri = f"{base_url}/api/v1/connections/shopify/auth/callback"
    
    logger.info("shopify_auth_url_generated", 
        shop=request.shop_url, 
        redirect_uri=redirect_uri, 
        dashboard_domain=settings.DASHBOARD_DOMAIN
    )
    
    auth_url = ShopifyConnector.get_auth_url(
        shop_domain=request.shop_url,
        state=state,
        redirect_uri=redirect_uri
    )
    
    return {"auth_url": auth_url}

@router.post("/auth/exchange", response_model=ConnectionResponse)
async def exchange_shopify_token(
    request: ShopifyExchangeRequest,
    db: Session = Depends(get_db)
):
    """
    Exchange Shopify authorization code for access token.
    Called by frontend after receiving callback.
    """
    # 1. Verify HMAC
    # Construct params dict for verification
    params = request.model_dump(exclude_none=True)
    # verify_hmac expects dict with all query params
    
    if not ShopifyConnector.verify_hmac(params):
        logger.warning("shopify_exchange_invalid_hmac", params=params)
        raise HTTPException(status_code=400, detail="Invalid HMAC signature")
        
    try:
        tenant_id = uuid.UUID(request.state)
    except ValueError:
        logger.error("shopify_exchange_invalid_state", state=request.state)
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # 2. Exchange token
    access_token, error = await ShopifyConnector.exchange_token(request.shop, request.code)
    if error:
        logger.error("shopify_exchange_token_failed", error=error)
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {error}")
        
    # 3. Verify connection and get details
    is_valid, shop_details = await ShopifyConnector.verify_connection(request.shop, access_token)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Failed to verify connection with Shopify")

    # 4. Save connection
    # Check if connection exists for this tenant
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.SHOPIFY.value
    ).first()

    config_data = {
        "shop_url": f"https://{request.shop}",
        "shop_info": shop_details
    }
    
    credentials_data = {
        "access_token": access_token
    }
    
    if connection:
        connection.credentials = credentials_data
        connection.config = config_data
        connection.is_active = True
        logger.info("shopify_connection_updated", tenant_id=str(tenant_id), shop=request.shop)
    else:
        connection = ChannelConnectionModel(
            tenant_id=tenant_id,
            channel_type=ChannelType.SHOPIFY.value,
            credentials=credentials_data,
            config=config_data,
            is_active=True
        )
        db.add(connection)
        logger.info("shopify_connection_created", tenant_id=str(tenant_id), shop=request.shop)
    
    db.commit()
    
    return ConnectionResponse(
        status="connected",
        message="Shopify connected successfully",
        details=shop_details
    )

@public_router.get("/auth/callback")
async def auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Shopify OAuth callback.
    """
    params = dict(request.query_params)
    
    # 1. Verify HMAC
    if not ShopifyConnector.verify_hmac(params):
        logger.warning("shopify_callback_invalid_hmac", params=params)
        raise HTTPException(status_code=400, detail="Invalid HMAC signature")
        
    shop = params.get("shop")
    code = params.get("code")
    state = params.get("state") # tenant_id
    
    if not shop or not code or not state:
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    try:
        tenant_id = uuid.UUID(state)
    except ValueError:
        logger.error("shopify_callback_invalid_state", state=state)
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # 2. Exchange token
    access_token, error = await ShopifyConnector.exchange_token(shop, code)
    if error:
        logger.error("shopify_callback_token_exchange_failed", error=error)
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {error}")
        
    # 3. Verify connection and get details
    is_valid, shop_details = await ShopifyConnector.verify_connection(shop, access_token)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Failed to verify connection with Shopify")

    # 4. Save connection
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.SHOPIFY.value
    ).first()

    config_data = {
        "shop_url": f"https://{shop}",
        "shop_info": shop_details
    }
    
    credentials_data = {
        "access_token": access_token
    }
    
    # Note: Credentials should be encrypted at rest. 
    # Assuming the database or a middleware handles field encryption, 
    # or this field is treated as sensitive.
    
    if connection:
        connection.credentials = credentials_data
        connection.config = config_data
        connection.is_active = True
        logger.info("shopify_connection_updated", tenant_id=str(tenant_id), shop=shop)
    else:
        connection = ChannelConnectionModel(
            tenant_id=tenant_id,
            channel_type=ChannelType.SHOPIFY.value,
            credentials=credentials_data,
            config=config_data,
            is_active=True
        )
        db.add(connection)
        logger.info("shopify_connection_created", tenant_id=str(tenant_id), shop=shop)
    
    db.commit()
    
    # 5. Redirect to frontend
    dashboard_url = settings.DASHBOARD_DOMAIN or "http://localhost:3000"
    return RedirectResponse(url=f"{dashboard_url}/marketing-studio/connections?status=success&channel=shopify")

@router.post("/disconnect", response_model=ConnectionResponse)
async def disconnect_shopify(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Deactivate Shopify connection.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.SHOPIFY.value
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="No Shopify connection found")

    connection.is_active = False
    # Optionally clear credentials for security, or keep them for easy reactivation
    # For now, we just deactivate
    
    db.commit()
    logger.info("shopify_connection_disconnected", tenant_id=str(user.tenant_id))

    return ConnectionResponse(
        status="disconnected",
        message="Shopify disconnected successfully"
    )

@router.post("/test", response_model=ConnectionResponse)
async def test_shopify_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test the current stored connection.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.SHOPIFY.value,
        ChannelConnectionModel.is_active.is_(True)
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="No active Shopify connection found")

    access_token = connection.credentials.get("access_token")
    shop_url = connection.config.get("shop_url")
    
    if not access_token or not shop_url:
        raise HTTPException(status_code=400, detail="Incomplete connection data")

    is_valid, result = await ShopifyConnector.verify_connection(
        shop_url=shop_url, 
        access_token=access_token
    )
    
    if is_valid:
        # Update shop info in config if successful, to keep it fresh
        connection.config["shop_info"] = result
        db.commit()
        return ConnectionResponse(
            status="active",
            message="Connection is valid",
            details=result
        )
    else:
        return ConnectionResponse(
            status="error",
            message="Connection test failed",
            details=result
        )
