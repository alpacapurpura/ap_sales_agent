"""Unit tests for collect_tenant_anchors — S11B step 6.

# [SALES-AGENT-TENANT-ROUTE-OVERLAY-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from luana_core_sales_agent.application.services.tenant_route_overlay import (
    collect_tenant_anchors,
)


def test_empty_offers_returns_empty_lists() -> None:
    routes, anchors = collect_tenant_anchors([])
    assert routes == []
    assert anchors == []


def test_offer_without_objections_skipped() -> None:
    routes, anchors = collect_tenant_anchors([{"name": "Curso A"}])
    assert routes == []
    assert anchors == []


def test_objection_with_phrases_emits_routes() -> None:
    offers = [
        {
            "objections": [
                {"type": "price", "trigger_phrases": ["es muy caro", "no me alcanza"]},
                {"type": "trust", "trigger_phrases": ["y si no funciona"]},
            ],
        },
    ]
    routes, anchors = collect_tenant_anchors(offers)
    assert routes == ["objection_price", "objection_price", "objection_trust"]
    assert anchors == ["es muy caro", "no me alcanza", "y si no funciona"]


def test_empty_phrases_filtered() -> None:
    offers = [
        {
            "objections": [
                {"type": "price", "trigger_phrases": ["", "  ", "real"]},
            ],
        },
    ]
    routes, anchors = collect_tenant_anchors(offers)
    assert routes == ["objection_price"]
    assert anchors == ["real"]


def test_objection_without_type_uses_custom() -> None:
    offers = [
        {
            "objections": [
                {"trigger_phrases": ["weird phrase"]},
            ],
        },
    ]
    routes, _ = collect_tenant_anchors(offers)
    assert routes == ["objection_custom"]


def test_phrases_stripped() -> None:
    offers = [
        {
            "objections": [
                {"type": "trust", "trigger_phrases": ["  espacios extra  "]},
            ],
        },
    ]
    _, anchors = collect_tenant_anchors(offers)
    assert anchors == ["espacios extra"]


def test_objection_without_trigger_phrases_skipped() -> None:
    offers = [{"objections": [{"type": "money"}]}]
    routes, anchors = collect_tenant_anchors(offers)
    assert routes == []
    assert anchors == []
