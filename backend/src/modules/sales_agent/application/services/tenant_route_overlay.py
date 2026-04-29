"""Tenant route overlay — per-tenant Offer ``trigger_phrases`` extension.

Carved out of ``SemanticRouter.register_tenant_routes`` (S11B step 6) so
the embedding cache mechanics live in the singleton router but the
*tenant logic* (offers → routes) is testable in isolation.

The overlay translates ``[{objections: [{type, trigger_phrases: [...]}]}]``
into ``({route_names}, {anchors})`` tuples ready to be fed to the
``TextEmbedding`` cache.

# [SALES-AGENT-TENANT-ROUTE-OVERLAY-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations


def collect_tenant_anchors(offers_data: list[dict]) -> tuple[list[str], list[str]]:
    """Flatten Offer ``objections.trigger_phrases`` into route_names + anchors.

    For each phrase ``p`` in ``offer["objections"][i]["trigger_phrases"]``,
    emits ``(route_name, anchor)`` where ``route_name = f"objection_{type}"``.
    Skips empty phrases. Returns parallel lists ready for embedding lookup.
    """
    route_names: list[str] = []
    anchors: list[str] = []

    for offer in offers_data:
        for obj in offer.get("objections", []):
            trigger_phrases = obj.get("trigger_phrases", [])
            if not trigger_phrases:
                continue
            route_name = f"objection_{obj.get('type', 'custom')}"
            for phrase in trigger_phrases:
                if phrase and phrase.strip():
                    route_names.append(route_name)
                    anchors.append(phrase.strip())

    return route_names, anchors


__all__ = ["collect_tenant_anchors"]
