from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.scheduling.application.services.event_type_service import (
    EventTypeService,
)
from src.modules.scheduling.domain.event_type_schema import EventType, EventTypeUpdate

router = APIRouter(tags=["event-types"])
logger = structlog.get_logger()


@router.get("")
async def list_event_types(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[EventType]:
    service = EventTypeService(db, user.tenant_id)
    return service.list_event_types()


@router.post("")
async def create_event_type(
    event_type: EventType,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EventType:
    service = EventTypeService(db, user.tenant_id)
    return service.create_event_type(event_type)


@router.patch("/{event_type_id}")
async def update_event_type(
    event_type_id: str,
    update: EventTypeUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> EventType:
    service = EventTypeService(db, user.tenant_id)
    updated = service.update_event_type(event_type_id, update)
    if not updated:
        raise HTTPException(status_code=404, detail="Event Type not found")
    return updated


@router.delete("/{event_type_id}")
async def delete_event_type(
    event_type_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    service = EventTypeService(db, user.tenant_id)
    deleted = service.delete_event_type(event_type_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event Type not found")
    return {"status": "deleted"}
