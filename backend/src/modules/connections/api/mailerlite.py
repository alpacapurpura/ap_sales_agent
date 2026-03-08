from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.connections.domain.enums import ChannelType
from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel
from src.modules.connections.infrastructure.marketing_connectors.mailerlite import MailerliteConnector
import structlog

logger = structlog.get_logger()
router = APIRouter()

# --- Pydantic Models ---

class MailerliteConnectRequest(BaseModel):
    api_key: str

class MailerliteStatusResponse(BaseModel):
    is_connected: bool
    account_info: Optional[Dict[str, Any]] = None

class ConnectionResponse(BaseModel):
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None

# --- Endpoints ---

@router.get("/status", response_model=MailerliteStatusResponse)
async def get_mailerlite_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Check if MailerLite is connected for the current tenant.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.MAILERLITE.value,
        ChannelConnectionModel.is_active.is_(True)
    ).first()

    if not connection:
        return MailerliteStatusResponse(is_connected=False)

    return MailerliteStatusResponse(
        is_connected=True,
        account_info=connection.config.get("account_info")
    )

@router.post("/connect", response_model=ConnectionResponse)
async def connect_mailerlite(
    request: MailerliteConnectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Connect or update MailerLite credentials.
    Verifies the connection with MailerLite API before saving.
    """
    # 1. Verify credentials with MailerLite
    is_valid, result = await MailerliteConnector.verify_connection(
        api_key=request.api_key
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect to MailerLite: {result.get('error')}"
        )

    # 2. Check existing connection
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.MAILERLITE.value
    ).first()

    config_data = {
        "account_info": result
    }
    
    credentials_data = {
        "api_key": request.api_key
    }

    if connection:
        # Update existing
        connection.credentials = credentials_data
        connection.config = config_data
        connection.is_active = True
        logger.info("mailerlite_connection_updated", tenant_id=str(user.tenant_id))
    else:
        # Create new
        connection = ChannelConnectionModel(
            tenant_id=user.tenant_id,
            channel_type=ChannelType.MAILERLITE.value,
            credentials=credentials_data,
            config=config_data,
            is_active=True
        )
        db.add(connection)
        logger.info("mailerlite_connection_created", tenant_id=str(user.tenant_id))
    
    db.commit()
    db.refresh(connection)

    return ConnectionResponse(
        status="connected",
        message="MailerLite connected successfully",
        details=result
    )

@router.post("/disconnect", response_model=ConnectionResponse)
async def disconnect_mailerlite(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Deactivate MailerLite connection.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.MAILERLITE.value
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="No MailerLite connection found")

    connection.is_active = False
    
    db.commit()
    logger.info("mailerlite_connection_disconnected", tenant_id=str(user.tenant_id))

    return ConnectionResponse(
        status="disconnected",
        message="MailerLite disconnected successfully"
    )

@router.post("/test", response_model=ConnectionResponse)
async def test_mailerlite_connection(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Test the current stored connection.
    """
    connection = db.query(ChannelConnectionModel).filter(
        ChannelConnectionModel.tenant_id == user.tenant_id,
        ChannelConnectionModel.channel_type == ChannelType.MAILERLITE.value,
        ChannelConnectionModel.is_active.is_(True)
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="No active MailerLite connection found")

    api_key = connection.credentials.get("api_key")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="Incomplete connection data")

    is_valid, result = await MailerliteConnector.verify_connection(
        api_key=api_key
    )
    
    if is_valid:
        # Update account info in config if successful
        connection.config["account_info"] = result
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
