from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import structlog

from src.services.database import get_db
from src.api.dependencies import get_current_user
from src.services.db.models.user import User
from src.services.db.models.channel_connection import ChannelConnection
from src.channels.gmail import GmailAdapter

router = APIRouter(prefix="/gmail", tags=["gmail"])
logger = structlog.get_logger()

# --- Schemas ---
class GmailStatusResponse(BaseModel):
    is_connected: bool
    email: Optional[str] = None

# --- Endpoints ---

@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    Get the Google OAuth2 authorization URL for Gmail.
    """
    url, state = GmailAdapter.get_authorization_url(redirect_uri)
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
    try:
        creds_data = GmailAdapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("gmail_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticación con Google")

    # Get email from profile to identify
    try:
        adapter = GmailAdapter(creds_data)
        profile = adapter.get_profile()
        email = profile.get('emailAddress')
        if not email:
            raise ValueError("Email address not found in profile")
    except Exception as e:
        logger.error("failed_to_get_gmail_profile", error=str(e))
        # If we can't get the profile, the token might be invalid or scopes missing
        raise HTTPException(status_code=400, detail="No se pudo obtener el perfil de Gmail. Verifica los permisos.")

    # Save to DB
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'gmail'
    ).first()

    if connection:
        connection.credentials = creds_data
        connection.config = {"email": email}
        connection.is_active = True
    else:
        connection = ChannelConnection(
            tenant_id=user.tenant_id,
            channel_type='gmail',
            credentials=creds_data,
            config={"email": email},
            is_active=True
        )
        db.add(connection)
    
    db.commit()
    return {"status": "connected", "email": email}

@router.get("/status", response_model=GmailStatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if Gmail is connected.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'gmail',
        ChannelConnection.is_active.is_(True)
    ).first()
    
    if not connection:
        return GmailStatusResponse(is_connected=False)
        
    return GmailStatusResponse(
        is_connected=True, 
        email=connection.config.get("email")
    )

@router.delete("/disconnect")
async def disconnect(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Disconnect Gmail.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'gmail'
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
    Test Gmail connection by fetching profile.
    """
    connection = db.query(ChannelConnection).filter(
        ChannelConnection.tenant_id == user.tenant_id,
        ChannelConnection.channel_type == 'gmail',
        ChannelConnection.is_active.is_(True)
    ).first()
    
    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Gmail no conectado")
        
    try:
        adapter = GmailAdapter(connection.credentials)
        profile = adapter.get_profile()
        return {"status": "ok", "message": "Conexión exitosa", "data": profile}
    except Exception as e:
        logger.error("gmail_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}
