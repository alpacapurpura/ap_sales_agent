"""TDD — SalesAgentSuggestionProvider: heuristic, route-scoped, tenant-isolated.

Tests written RED first per ``tdd-mandatory.md``.
Uses mocks — no DB required.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

_VOSEO_RE = re.compile(
    r"\b(sos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|"
    r"elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|subí|"
    r"bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|ejecutás|acompañás|activás|"
    r"desactivás|linkeá|listá|probá|mostrá|compartí|contá|explicá)\b",
    re.IGNORECASE,
)

_TENANT = uuid4()


def _ctx(route: str | None = "sales", tenant_id=None):
    from luana_core_copilot.domain.suggestion import SuggestionContext

    return SuggestionContext(
        tenant_id=tenant_id or _TENANT,
        user_id=None,
        conversation_id=None,
        current_route=route,
    )


def _mock_sa_port(
    leads_7d: int = 5,
    leads_30d: int = 10,
    active_24h: int = 3,
    enrollments_by_status: dict | None = None,
) -> MagicMock:
    """Return a mock SalesAgentObservabilityPort."""
    port = MagicMock()

    call_count = {"count": 0}

    def _count_leads_since(tenant_id, since):
        call_count["count"] += 1
        # First call = 7d window, second = 30d window
        if call_count["count"] == 1:
            return leads_7d
        return leads_30d

    def _count_active_since(tenant_id, since):
        return active_24h

    enrollments_by_status = enrollments_by_status or {}

    def _list_by_status(tenant_id, statuses):
        from luana_core_platform.links.ports.sales_agent import EnrollmentSummaryDTO

        result = []
        for status in statuses:
            for item in enrollments_by_status.get(status, []):
                result.append(
                    EnrollmentSummaryDTO(
                        id=str(uuid4()),
                        offer_id=str(uuid4()),
                        status=status,
                        created_at_iso=item.get("created_at_iso", "2024-01-01T00:00:00"),
                        edition_id=None,
                    )
                )
        return result

    port.count_leads_since.side_effect = _count_leads_since
    port.count_active_conversations_since.side_effect = _count_active_since
    port.list_enrollments_by_status.side_effect = _list_by_status
    port.has_active_edition_for_offer.return_value = True
    return port


def _mock_brand_port(personality_present: bool = True) -> MagicMock:
    from luana_core_platform.links.ports.brand import BrandKnowledgeDTO

    port = MagicMock()
    port.get_brand_knowledge.return_value = BrandKnowledgeDTO(
        brand_data={},
        avatars=[],
        personality_profile=None,
    )
    port.get_buyer_persona_count.return_value = 1
    port.get_active_personality_profile_present.return_value = personality_present
    return port


class TestSalesAgentProviderMetadata:
    def test_sales_provider_metadata(self) -> None:
        """provider_id, provider_priority, applies_to_routes contract."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        p = SalesAgentSuggestionProvider()
        assert p.provider_id == "sales_agent"
        assert p.provider_priority == 10
        assert p.applies_to_routes == ("sales",)


class TestSalesAgentProviderRules:
    def test_sales_provider_no_leads_7d_emits_chip(self) -> None:
        """count_leads_since(7d) == 0 → 'Sin leads esta semana' chip."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        sa_port = _mock_sa_port(leads_7d=0, leads_30d=0, active_24h=0)
        brand_port = _mock_brand_port(personality_present=True)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert any("leads" in l.lower() or "sin leads" in l.lower() for l in labels), (
            f"Expected 'Sin leads' chip in {labels}"
        )

    def test_sales_provider_inactive_24h_with_old_leads_emits_reactivation_chip(self) -> None:
        """active_24h=0 + leads_30d>0 → reactivation chip."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        sa_port = _mock_sa_port(leads_7d=3, leads_30d=8, active_24h=0)
        brand_port = _mock_brand_port(personality_present=True)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert any("reactiv" in l.lower() or "inactiv" in l.lower() for l in labels), (
            f"Expected reactivation chip in {labels}"
        )

    def test_sales_provider_no_personality_profile_emits_voice_chip(self) -> None:
        """personality_present=False → 'Configura la voz del sales agent' chip."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        sa_port = _mock_sa_port(leads_7d=5, leads_30d=10, active_24h=2)
        brand_port = _mock_brand_port(personality_present=False)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert any("voz" in l.lower() for l in labels), f"Expected voice chip in {labels}"

    def test_sales_provider_pending_payments_emits_chip(self) -> None:
        """PAYMENT_PENDING enrollments >24h old → cobros chip."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        old_date = "2024-01-01T00:00:00"
        enrollments = {
            "payment_pending": [
                {"created_at_iso": old_date},
                {"created_at_iso": old_date},
                {"created_at_iso": old_date},
            ]
        }
        sa_port = _mock_sa_port(leads_7d=5, leads_30d=10, active_24h=2, enrollments_by_status=enrollments)
        brand_port = _mock_brand_port(personality_present=True)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert any("cobro" in l.lower() or "pago" in l.lower() or "pendiente" in l.lower() for l in labels), (
            f"Expected cobros chip in {labels}"
        )

    def test_sales_provider_waitlist_no_active_edition_emits_chip(self) -> None:
        """Waitlist enrollments + no active edition → lista espera chip."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        enrollments = {
            "waitlist": [
                {"created_at_iso": "2024-01-01T00:00:00"},
            ]
        }
        sa_port = _mock_sa_port(leads_7d=5, leads_30d=10, active_24h=2, enrollments_by_status=enrollments)
        sa_port.has_active_edition_for_offer.return_value = False
        brand_port = _mock_brand_port(personality_present=True)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert any("espera" in l.lower() or "waitlist" in l.lower() or "edición" in l.lower() for l in labels), (
            f"Expected waitlist chip in {labels}"
        )

    def test_sales_provider_port_exception_degrades_gracefully(self) -> None:
        """SA port raises → _safe_* wrappers return safe defaults (0 leads → rule-1 chip).

        Design: per-call resilience via _safe_int/_safe_bool/_safe_list lets
        provider degrade to conservative chips even if individual port calls
        fail. User sees "Sin leads esta semana" whether port outage OR
        genuine zero leads — same actionable message.
        """
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        sa_port = MagicMock()
        sa_port.count_leads_since.side_effect = RuntimeError("Connection failed")
        sa_port.count_active_conversations_since.side_effect = RuntimeError("Connection failed")
        sa_port.list_enrollments_by_status.side_effect = RuntimeError("Connection failed")
        sa_port.has_active_edition_for_offer.side_effect = RuntimeError("Connection failed")
        brand_port = _mock_brand_port()
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        # Resilient degradation: rule-1 fires (leads_7d == 0 from safe default)
        labels = [c.label.lower() for c in chips]
        assert any("leads esta semana" in lbl for lbl in labels), (
            f"Expected resilient rule-1 chip when port outage, got {labels}"
        )

    def test_sales_provider_tenant_isolation(self) -> None:
        """Provider passes tenant_id from ctx — no cross-tenant leak."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        tenant_a = uuid4()
        sa_port = _mock_sa_port(leads_7d=5, leads_30d=10, active_24h=2)
        brand_port = _mock_brand_port(personality_present=True)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            p.get_suggestions(_ctx(tenant_id=tenant_a))

        # Every port call must use the correct tenant
        for call_args in sa_port.count_leads_since.call_args_list:
            assert call_args[0][0] == tenant_a or call_args.args[0] == tenant_a


class TestSalesAgentProviderSpanishNeutro:
    def test_no_voseo_in_chip_labels_and_prompts(self) -> None:
        """All chip labels/prompts respect Spanish neutro LatAm."""
        from luana_core_copilot.application.suggestions.providers.sales_agent import (
            SalesAgentSuggestionProvider,
        )

        sa_port = _mock_sa_port(leads_7d=0, leads_30d=0, active_24h=0)
        sa_port.list_enrollments_by_status.return_value = []
        sa_port.has_active_edition_for_offer.return_value = False
        brand_port = _mock_brand_port(personality_present=False)
        with (
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_sales_agent_observability_port",
                return_value=sa_port,
            ),
            patch(
                "luana_core_copilot.application.suggestions.providers.sales_agent.create_brand_data_port",
                return_value=brand_port,
            ),
        ):
            p = SalesAgentSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        for chip in chips:
            assert not _VOSEO_RE.search(chip.label), f"Voseo in label: {chip.label!r}"
            assert not _VOSEO_RE.search(chip.prompt), f"Voseo in prompt: {chip.prompt!r}"
