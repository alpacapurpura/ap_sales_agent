import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.scheduling.domain.event_type_schema import EventType, EventTypeUpdate

logger = logging.getLogger(__name__)

class EventTypeService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _get_tenant(self) -> TenantModel:
        return self.db.query(TenantModel).filter(TenantModel.id == self.tenant_id).first()

    def _migrate_event_type(self, data: dict) -> dict:
        """
        Migrate legacy EventType structure.
        """
        # Ensure ID exists
        if not data.get('id'):
            data['id'] = str(uuid.uuid4())

        # is_active -> is_hidden
        if 'is_active' in data:
            # Logic inversion: is_active=True -> is_hidden=False
            data['is_hidden'] = not data.pop('is_active')
            
        # Ensure new config fields exist if missing
        if 'scheduling_limits' not in data:
            data['scheduling_limits'] = {"max_advance_days": 60, "min_advance_hours": 4}
        if 'booking_config' not in data:
            data['booking_config'] = {"buffer_minutes": 30, "max_per_day": None, "guest_permissions": True}
        if 'confirmation_button' not in data:
            data['confirmation_button'] = {"enabled": False}
            
        return data

    def list_event_types(self) -> List[EventType]:
        tenant = self._get_tenant()
        if not tenant:
            return []
        
        config = tenant.config_json or {}
        event_types_data = config.get('event_types', [])
        results = []
        for et in event_types_data:
            try:
                data = self._migrate_event_type(et.copy())
                results.append(EventType(**data))
            except Exception as e:
                logger.error(f"Failed to migrate event type {et.get('id', 'unknown')}: {e}")
                continue
        return results

    def get_event_type(self, event_type_id: str) -> Optional[EventType]:
        tenant = self._get_tenant()
        if not tenant:
            return None
        
        config = tenant.config_json or {}
        event_types_data = config.get('event_types', [])
        data = next((et.copy() for et in event_types_data if et['id'] == event_type_id), None)
        if data:
            data = self._migrate_event_type(data)
            return EventType(**data)
        return None
    
    def get_by_slug(self, slug: str) -> Optional[EventType]:
        tenant = self._get_tenant()
        if not tenant:
            return None
            
        config = tenant.config_json or {}
        event_types_data = config.get('event_types', [])
        data = next((et.copy() for et in event_types_data if et['slug'] == slug), None)
        if data:
            data = self._migrate_event_type(data)
            return EventType(**data)
        return None

    def create_event_type(self, event_type: EventType) -> EventType:
        tenant = self._get_tenant()
        config = dict(tenant.config_json or {})
        event_types = config.get('event_types', [])
        
        # Ensure slug uniqueness
        original_slug = event_type.slug
        counter = 1
        while any(et['slug'] == event_type.slug for et in event_types):
            event_type.slug = f"{original_slug}-{counter}"
            counter += 1
        
        event_types.append(event_type.dict())
        config['event_types'] = event_types
        
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        self.db.commit()
        self.db.refresh(tenant)
        return event_type

    def update_event_type(self, event_type_id: str, update: EventTypeUpdate) -> Optional[EventType]:
        tenant = self._get_tenant()
        config = dict(tenant.config_json or {})
        event_types = config.get('event_types', [])
        
        target_idx = next((i for i, et in enumerate(event_types) if et['id'] == event_type_id), None)
        if target_idx is None:
            return None
        
        current = event_types[target_idx]
        
        # Merge updates
        update_data = update.model_dump(exclude_unset=True)
        
        # Handle slug update with uniqueness check if changed
        if 'slug' in update_data and update_data['slug'] != current['slug']:
            new_slug = update_data['slug']
            original_slug = new_slug
            counter = 1
            # Check against OTHER event types
            while any(et['slug'] == new_slug for i, et in enumerate(event_types) if i != target_idx):
                new_slug = f"{original_slug}-{counter}"
                counter += 1
            update_data['slug'] = new_slug

        # Nested Pydantic models need special handling if we want to merge instead of replace
        # But here EventTypeUpdate uses Optional[SchedulingLimits], so if provided, it replaces the whole object usually.
        # However, for deeper partial updates, we might need manual merging. 
        # Given the frontend sends the whole object structure for nested fields usually, replacing is fine.
        
        current.update(update_data)
        
        event_types[target_idx] = current
        config['event_types'] = event_types
        
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        self.db.commit()
        
        return EventType(**current)

    def delete_event_type(self, event_type_id: str) -> bool:
        tenant = self._get_tenant()
        config = dict(tenant.config_json or {})
        event_types = config.get('event_types', [])
        
        new_event_types = [et for et in event_types if et['id'] != event_type_id]
        
        if len(new_event_types) == len(event_types):
            return False
            
        config['event_types'] = new_event_types
        tenant.config_json = config
        flag_modified(tenant, "config_json")
        self.db.commit()
        return True
