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
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

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
    """Handle churn_detected events by setting lifecycle_stage=CHURNED."""
    try:
        from src.core.database import SessionLocal
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        db = SessionLocal()
        try:
            svc = LifecycleService(db)
            svc.handle_churn_event(event)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception:
        logger.exception(
            "Failed to handle churn_detected event for tenant %s, profile %s",
            event.tenant_id,
            event.payload.get("profile_id"),
        )


def handle_lead_captured_event(event: DomainEvent) -> None:
    """Handle LeadCapturedEvent -- currently analytics-only (no CRM side effect needed).

    The LeadCapturedEvent is emitted by ChatOrchestrator AFTER CustomerService.identify()
    has already created the profile with lead_source set. This handler exists for:
    1. Logging/auditing lead capture events
    2. Future: triggering welcome sequences, lead scoring recalculation, etc.
    """
    logger.info(
        "Lead captured: profile=%s channel=%s field=%s tenant=%s",
        event.payload.get("profile_id"),
        event.payload.get("channel_slug"),
        event.payload.get("extracted_field"),
        event.tenant_id,
    )


def _handle_appointment_event(event: DomainEvent, journey_event_name: str) -> None:
    """Create a journey_event from an appointment EventBus event.

    Resolves lead_id -> customer_profile (if mapping exists) and creates
    the journey_event with meeting details in properties. If no profile
    found, the event is still recorded with lead_id in properties for
    later reconciliation.
    """
    try:
        from uuid import UUID

        from sqlalchemy import select

        from src.core.database import SessionLocal
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )
        from src.modules.crm.infrastructure.models.customer_model import (
            CustomerProfileModel,
            JourneyEventModel,
        )
        from src.modules.crm.infrastructure.models.lead_model import LeadModel

        db = SessionLocal()
        try:
            lead_id = event.payload.get("lead_id")
            appointment_id = event.payload.get("appointment_id")
            status = event.payload.get("status")

            # Try to resolve profile from lead's email
            profile = None
            if lead_id:
                lead = db.execute(
                    select(LeadModel).where(LeadModel.id == UUID(lead_id)),
                ).scalar_one_or_none()

                if lead and lead.email:
                    profile = db.execute(
                        select(CustomerProfileModel).where(
                            CustomerProfileModel.tenant_id == event.tenant_id,
                            CustomerProfileModel.primary_email == lead.email,
                            CustomerProfileModel.is_inactive == False,
                        ),
                    ).scalar_one_or_none()

            properties = {
                "source": "scheduling",
                "appointment_id": str(appointment_id) if appointment_id else "",
                "lead_id": str(lead_id) if lead_id else "",
                "status": status or "",
            }

            if profile:
                je = JourneyEventModel(
                    profile_id=profile.id,
                    tenant_id=event.tenant_id,
                    event_name=journey_event_name,
                    event_type="track",
                    properties=properties,
                )
                db.add(je)

                # Recalculate score (meeting_requested = +10.0 pts)
                svc = LifecycleService(db)
                svc.recalculate_score(profile.id, event.tenant_id)
            else:
                # No profile found -- still record for reconciliation
                logger.warning(
                    "Appointment event without matching profile: lead_id=%s event=%s",
                    lead_id,
                    journey_event_name,
                )

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception:
        logger.exception(
            "Failed to handle %s event for tenant %s",
            journey_event_name,
            event.tenant_id,
        )


def handle_appointment_booked(event: DomainEvent) -> None:
    """Handle appointment_booked event: create meeting_booked journey_event."""
    _handle_appointment_event(event, "meeting_booked")


def handle_appointment_completed(event: DomainEvent) -> None:
    """Handle appointment_completed event: create meeting_completed journey_event."""
    _handle_appointment_event(event, "meeting_completed")


def handle_appointment_no_show(event: DomainEvent) -> None:
    """Handle appointment_no_show event: create meeting_no_show journey_event."""
    _handle_appointment_event(event, "meeting_no_show")


def register_event_handlers() -> None:
    """Register all CRM event handlers. Call once at app startup."""
    EventBus.subscribe("sale_completed", handle_sale_completed_event)
    EventBus.subscribe("churn_detected", handle_churn_event)
    EventBus.subscribe("lead_captured", handle_lead_captured_event)
    EventBus.subscribe("appointment_booked", handle_appointment_booked)
    EventBus.subscribe("appointment_completed", handle_appointment_completed)
    EventBus.subscribe("appointment_no_show", handle_appointment_no_show)
    logger.info(
        "CRM event handlers registered: sale_completed, churn_detected, "
        "lead_captured, appointment_booked, appointment_completed, appointment_no_show",
    )
