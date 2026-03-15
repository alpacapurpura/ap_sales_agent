"""
CRM event handler registration.

Subscribes to domain events via the shared EventBus.
Called once at app startup via register_event_handlers().

Handler exceptions are caught and logged -- never propagated to the publisher.
"""
import logging

from src.shared.domain.events import DomainEvent, EventBus

logger = logging.getLogger(__name__)


def handle_sale_completed_event(event: DomainEvent) -> None:
    """Handle sale_completed events by transitioning the customer's lifecycle."""
    try:
        from src.core.database import SessionLocal
        from src.modules.crm.application.services.lifecycle_service import LifecycleService

        db = SessionLocal()
        try:
            svc = LifecycleService(db)
            svc.handle_sale_completed(event)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception:
        logger.exception(
            "Failed to handle sale_completed event for tenant %s",
            event.tenant_id,
        )


def handle_churn_event(event: DomainEvent) -> None:
    """Placeholder for churn_detected events. Implementation in Plan 03."""
    logger.info(
        "Churn event received for tenant %s, profile %s (handler not yet implemented)",
        event.tenant_id,
        event.payload.get("profile_id"),
    )


def register_event_handlers() -> None:
    """Register all CRM event handlers. Call once at app startup."""
    EventBus.subscribe("sale_completed", handle_sale_completed_event)
    EventBus.subscribe("churn_detected", handle_churn_event)
    logger.info("CRM event handlers registered: sale_completed, churn_detected")
