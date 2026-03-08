from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import structlog
import logging
from pydantic import BaseModel

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel
from src.modules.connections.infrastructure.channels.google_analytics import GoogleAnalyticsAdapter
from src.modules.connections.api.dto.google_analytics import GoogleAnalyticsStatusResponse

router = APIRouter(tags=["google_analytics"])
logger = structlog.get_logger()

class GoogleAnalyticsConfig(BaseModel):
    client_id: str
    client_secret: str

# --- Endpoints ---

@router.put("/config")
async def save_config(
    config: GoogleAnalyticsConfig,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Save Google Analytics client configuration (client_id, client_secret).
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics'
    ).first()

    creds_update = {"client_id": config.client_id, "client_secret": config.client_secret}
    
    if connection:
        # Preserve existing tokens if any, but update client config
        existing_creds = dict(connection.credentials) if connection.credentials else {}
        existing_creds.update(creds_update)
        connection.credentials = existing_creds
    else:
        connection = ChannelConnectionModel(
            tenant_id=user.tenant_id,
            channel_type='google_analytics',
            credentials=creds_update,
            config={},
            is_active=False
        )
        db.add(connection)
    
    db.commit()
    return {"status": "config_saved"}

@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get the Google OAuth2 authorization URL for Google Analytics.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics'
    ).first()

    if not connection or not connection.credentials or \
       'client_id' not in connection.credentials or 'client_secret' not in connection.credentials:
        raise HTTPException(status_code=400, detail="Configuración de cliente no encontrada. Configure client_id y client_secret primero.")

    client_config = {
        "client_id": connection.credentials['client_id'],
        "client_secret": connection.credentials['client_secret']
    }
    
    adapter = GoogleAnalyticsAdapter(client_config=client_config)
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}

@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Exchange the authorization code for tokens and save connection.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics'
    ).first()

    if not connection or not connection.credentials or \
       'client_id' not in connection.credentials or 'client_secret' not in connection.credentials:
        raise HTTPException(status_code=400, detail="Configuración de cliente no encontrada.")

    client_config = {
        "client_id": connection.credentials['client_id'],
        "client_secret": connection.credentials['client_secret']
    }

    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config)
        token_data = adapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("google_analytics_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticación con Google")

    # Merge token data with existing credentials (client_id/secret)
    full_creds = dict(connection.credentials)
    full_creds.update(token_data)

    # Get account summaries to verify access and store basic info if needed
    try:
        # Re-instantiate with full credentials
        adapter = GoogleAnalyticsAdapter(client_config=client_config, credentials_data=full_creds)
        summaries = adapter.get_account_summaries()
    except Exception as e:
        logger.error("failed_to_get_google_analytics_summaries", error=str(e))
        # If we can't get summaries, the token might be invalid or scopes missing
        raise HTTPException(status_code=400, detail="No se pudo obtener información de Google Analytics. Verifica los permisos.")

    # Update DB
    connection.credentials = full_creds
    connection.config = {"account_count": len(summaries)}
    connection.is_active = True
    
    db.commit()
    return {"status": "connected", "account_count": len(summaries)}

@router.get("/status", response_model=GoogleAnalyticsStatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if Google Analytics is connected.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics',
        ChannelConnectionModel.is_active.is_(True)
    ).first()
    
    if not connection:
        return GoogleAnalyticsStatusResponse(is_connected=False)
        
    return GoogleAnalyticsStatusResponse(
        is_connected=True, 
        account_summary=[] # We don't store full summary, maybe fetch fresh if needed but costly
    )

@router.delete("/disconnect")
async def disconnect(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Google Analytics.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics'
    ).first()
    
    if connection:
        db.delete(connection)
        db.commit()
        
    return {"status": "disconnected"}

@router.post("/test")
async def test_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test Google Analytics connection by fetching account summaries.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics',
        ChannelConnectionModel.is_active.is_(True)
    ).first()
    
    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")
    
    client_config = {
        "client_id": connection.credentials.get('client_id'),
        "client_secret": connection.credentials.get('client_secret')
    }
    
    if not client_config['client_id'] or not client_config['client_secret']:
         raise HTTPException(status_code=400, detail="Configuración incompleta")

    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config, credentials_data=connection.credentials)
        summaries = adapter.get_account_summaries()
        return {"status": "ok", "message": "Conexión exitosa", "data": summaries}
    except Exception as e:
        logger.error("google_analytics_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

@router.get("/properties")
async def get_properties(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get available Google Analytics properties.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == 'google_analytics',
        ChannelConnectionModel.is_active.is_(True)
    ).first()
    
    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Google Analytics no conectado")

    client_config = {
        "client_id": connection.credentials.get('client_id'),
        "client_secret": connection.credentials.get('client_secret')
    }
    
    if not client_config['client_id'] or not client_config['client_secret']:
         raise HTTPException(status_code=400, detail="Configuración incompleta")
        
    try:
        adapter = GoogleAnalyticsAdapter(client_config=client_config, credentials_data=connection.credentials)
        summaries = adapter.get_account_summaries()
        return summaries
    except Exception as e:
        logger.error("google_analytics_properties_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error al obtener propiedades")
