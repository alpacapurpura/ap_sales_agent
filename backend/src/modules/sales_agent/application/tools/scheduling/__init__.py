"""Scheduling toolkit for the sales agent (S8).

Three tools the LLM can request via ``[TOOL_REQUEST: {"tool": "<name>"}]``:

* ``create_booking_link``       — single-use, lead-scoped booking URL.
* ``verify_booking_status``     — check status (pending/confirmed/...) by tracking_id.
* ``get_available_slots``       — list upcoming slots for an event slug.

Strategy pattern: ``SchedulerProvider`` Protocol + ``InternalSchedulerProvider``
(default — uses Nicolify's own ``BookingLink`` + ``AvailabilityService``).

Future external providers (Cal.com / Calendly / Google Calendar push) plug
in via the ``SCHEDULER_PROVIDERS`` registry plus a matching
``WebhookProvider`` (see ``webhook_providers.py``).
"""

# [SALES-AGENT-S8-PROVIDER]  # noqa: ERA001

from src.modules.sales_agent.application.tools.scheduling.providers import (
    BookingLinkOutput,
    BookingStatus,
    BookingStatusValue,
    InternalSchedulerProvider,
    SchedulerProvider,
    SchedulerSlot,
    scheduler_provider_for_tenant,
)
from src.modules.sales_agent.application.tools.scheduling.tools import (
    SCHEDULING_TOOL_REGISTRY,
    tool_create_booking_link,
    tool_get_available_slots,
    tool_verify_booking_status,
)
from src.modules.sales_agent.application.tools.scheduling.webhook_providers import (
    SCHEDULER_WEBHOOK_PROVIDERS,
    ParsedWebhookEvent,
    WebhookEventType,
    WebhookProvider,
    register_webhook_provider,
    webhook_provider_for,
)

__all__ = [
    "SCHEDULER_WEBHOOK_PROVIDERS",
    "SCHEDULING_TOOL_REGISTRY",
    "BookingLinkOutput",
    "BookingStatus",
    "BookingStatusValue",
    "InternalSchedulerProvider",
    "ParsedWebhookEvent",
    "SchedulerProvider",
    "SchedulerSlot",
    "WebhookEventType",
    "WebhookProvider",
    "register_webhook_provider",
    "scheduler_provider_for_tenant",
    "tool_create_booking_link",
    "tool_get_available_slots",
    "tool_verify_booking_status",
    "webhook_provider_for",
]
