"""IdentityResolver — customer/lead identity for the chat flow.

Carved out of :class:`ChatOrchestrator` (S11B Strangler Fig step 2).
Owns the lookup-or-create lifecycle for both customer profiles (CRM
identity) and leads (sales_agent identity), the Instagram profile
enrichment side-effect, and the trait-merge logic.

Boundary: this class talks to ``IdentityService`` + ``LeadRepository`` +
``shared/links/ports/`` (channel adapter, IG enricher, journey events).
It does NOT know about state checkpoints, prompts, or LLM dispatch —
that lives in :class:`ConversationPipeline` (S11B step 3). It DOES know
about :class:`AuditEmitter` to publish ``lead_captured`` and track
``message_received`` for newly resolved customers.

Cross-module models (``CustomerProfileModel``, ``LeadModel``,
``IdentityService``, ``LeadRepository``) stay opaque (``Any``) so the
``sales_agent -> crm`` arch ratchet count remains frozen — runtime
duck typing handles the actual instances.

# [SALES-AGENT-IDENTITY-RESOLVER-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.orchestrator.audit_emitter import AuditEmitter
from src.shared.domain.enums import IdentityType
from src.shared.domain.events import CHANNEL_TYPE_TO_CAPTURE_SLUG

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.domain.messages import IncomingMessage

# Cross-module facades stay opaque (see audit_emitter.py rationale).
_CustomerProfile = Any
_Lead = Any
_IdentityService = Any
_LeadRepository = Any

logger = structlog.get_logger()


class IdentityResolver:
    """Resolve / enrich customer + lead identity for an incoming message.

    Stateless static class. The orchestrator instantiates nothing; it
    just calls these methods in the order dictated by the flow.
    """

    @staticmethod
    def resolve_customer(
        identity_service: _IdentityService,
        incoming: IncomingMessage,
        tenant_uuid: UUID | None,
    ) -> tuple[_CustomerProfile, bool, str, str, IdentityType]:
        """Lookup or create the customer profile from the incoming message.

        Returns ``(customer, was_created, capture_slug, channel_type, identity_type)``.
        """
        channel_type = incoming.channel_type
        try:
            identity_type = IdentityType(channel_type)
        except ValueError:
            identity_type = IdentityType.EXTERNAL_ID

        profile_data = {
            "first_name": incoming.metadata.get("first_name"),
            "last_name": incoming.metadata.get("last_name"),
            "traits": incoming.metadata,
        }

        capture_slug = CHANNEL_TYPE_TO_CAPTURE_SLUG.get(channel_type, channel_type)
        customer, was_created = identity_service.get_or_create_customer(
            tenant_id=tenant_uuid,
            identity_type=identity_type,
            identity_value=incoming.user_id,
            profile_data=profile_data,
            lead_source=capture_slug,
            lead_source_detail=channel_type,
        )
        return customer, was_created, capture_slug, channel_type, identity_type

    @staticmethod
    async def enrich_instagram_profile(
        db: Session,
        tenant_uuid: UUID,
        user_id_str: str,
        customer: _CustomerProfile,
        was_created: bool,
    ) -> None:
        """Pull name/username/avatar from the IG User Profile API for new IG leads."""
        if not (was_created or not (customer.traits or {}).get("instagram_username")):
            return
        try:
            from src.shared.links.ports.channel_adapter import create_connection_port
            from src.shared.links.ports.crm_repos import get_ig_profile_enricher

            connection_port = create_connection_port(db)
            creds = await connection_port.get_credentials(tenant_uuid, "meta")
            enricher = get_ig_profile_enricher(db)
            await enricher.enrich(
                tenant_id=tenant_uuid,
                igsid=user_id_str,
                customer_profile_id=customer.id,
                access_token=creds.credentials.get("access_token", ""),
            )
        except Exception:  # noqa: BLE001 — orchestrator resilience
            logger.warning("ig_profile_enrichment_failed", exc_info=True)

    @staticmethod
    def update_customer_traits(
        db: Session,
        customer: _CustomerProfile,
        incoming: IncomingMessage,
    ) -> None:
        """Merge incoming metadata into ``CustomerProfileModel.traits``."""
        if not incoming.metadata:
            return
        current_traits = dict(customer.traits) if customer.traits else {}
        needs_update = False
        for k, v in incoming.metadata.items():
            if k not in current_traits or current_traits[k] != v:
                current_traits[k] = v
                needs_update = True

        if not needs_update:
            return

        from src.shared.infrastructure.models.crm import CustomerProfileModel

        profile_model = (
            db.execute(
                select(CustomerProfileModel).where(
                    CustomerProfileModel.id == customer.id,
                ),
            )
            .scalars()
            .first()
        )
        if profile_model:
            profile_model.traits = current_traits
            if "first_name" in incoming.metadata:
                profile_model.full_name = (
                    f"{incoming.metadata.get('first_name', '')} {incoming.metadata.get('last_name', '')}".strip()
                )
            db.commit()

    @staticmethod
    def resolve_lead(
        lead_repo: _LeadRepository,
        customer_id: UUID,
        channel_type: str,
        user_id_str: str,
    ) -> _Lead:
        """Get the active lead for the customer or create one."""
        user = lead_repo.get_active_lead(customer_id)
        if not user:
            user = lead_repo.create_lead(
                customer_id=customer_id,
                channel=channel_type,
                channel_user_id=user_id_str,
            )
        return user

    @staticmethod
    async def process_customer_lifecycle(
        db: Session,
        identity_service: _IdentityService,
        incoming: IncomingMessage,
        tenant_uuid: UUID | None,
    ) -> tuple[_CustomerProfile, bool, str, str]:
        """Run the full identity lifecycle for an incoming message.

        Steps: resolve customer, enrich IG (when applicable), track
        ``message_received``, publish ``lead_captured`` for new customers,
        merge traits. Returns ``(customer, was_created, capture_slug,
        channel_type)``.
        """
        customer, was_created, capture_slug, channel_type, _ = IdentityResolver.resolve_customer(
            identity_service,
            incoming,
            tenant_uuid,
        )

        if channel_type == "instagram" and tenant_uuid:
            await IdentityResolver.enrich_instagram_profile(
                db,
                tenant_uuid,
                incoming.user_id,
                customer,
                was_created,
            )

        if tenant_uuid:
            AuditEmitter.track_message_received(
                db,
                tenant_uuid,
                customer,
                capture_slug,
                channel_type,
                incoming,
            )
        if was_created and tenant_uuid:
            AuditEmitter.publish_lead_captured(
                db,
                tenant_uuid,
                customer,
                capture_slug,
                channel_type,
            )

        IdentityResolver.update_customer_traits(db, customer, incoming)
        return customer, was_created, capture_slug, channel_type


__all__ = ["IdentityResolver"]
