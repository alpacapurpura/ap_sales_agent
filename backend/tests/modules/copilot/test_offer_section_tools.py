"""Tests for offer_section_tools — 17 tools, happy path + missing data edge cases.

Architecture:
- Mocks SessionLocal and get_tenant_id so no DB is touched.
- Mocks all lazy-imported repos via patch on the full import path.
- Verifies tenant isolation: cross-reading tools pass tenant_id to repos.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.modules.copilot.application.tools.offer_section_tools import (
    OFFER_SECTION_TOOLS,
    adapt_from_brand_identity,
    adapt_from_brand_narrative,
    assemble_from_brand_authority,
    detect_currency_mismatch,
    detect_hybrid_split,
    generate_from_preset_flags,
    high_ticket_tiering_template,
    import_from_brand_vault,
    import_scheduling_event_type,
    inherit_brand_methodology,
    pull_sales_agent_common_questions,
    recurring_billing_setup,
    reuse_brand_buyer_personas,
    reuse_brand_team,
    rewrite_tones,
    suggest_missing_objections,
    validate_preset_coherence,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid.uuid4()


def _make_brand_identity(brand_name: str = "Acme", tagline: str = "El mejor", voice_tone: str = "cercano") -> MagicMock:
    identity = MagicMock()
    identity.brand_name = brand_name
    identity.tagline = tagline
    identity.voice_tone = voice_tone
    return identity


def _make_brand_settings(
    identity: object | None = None,
    narrative: object | None = None,
    strategy: object | None = None,
    team: list | None = None,
) -> MagicMock:
    settings = MagicMock()
    settings.identity = identity if identity is not None else _make_brand_identity()
    settings.narrative = narrative
    settings.strategy = strategy
    settings.team = team or []
    settings.testimonials = []
    settings.authority_vault = []
    return settings


def _make_narrative(one_liner: str = "Transforma tu vida en 30 días.") -> MagicMock:
    hero = MagicMock()
    hero.identity = "emprendedores"
    hero.desire = "escalar su negocio"
    guide = MagicMock()
    guide.empathy_statement = "Entendemos lo difícil que es crecer sin sistema."
    outcome = MagicMock()
    outcome.transformation = "un negocio rentable con equipo"
    narrative = MagicMock()
    narrative.one_liner = one_liner
    narrative.hero = hero
    narrative.guide = guide
    narrative.outcome = outcome
    return narrative


def _make_strategy(name: str = "Metodología 3P", description: str = "Preparar, Publicar, Prosperar") -> MagicMock:
    pillar = MagicMock()
    pillar.name = "Pilar 1"
    pillar.description = "Descripción pilar 1"
    strategy = MagicMock()
    strategy.methodology_name = name
    strategy.methodology_description = description
    strategy.methodology_pillars = [pillar]
    return strategy


def _make_avatar(
    name: str = "Emprendedor Digital", is_default: bool = True, icp: str = "Profesional 30-45 años"
) -> MagicMock:
    av = MagicMock()
    av.name = name
    av.is_default = is_default
    av.icp_description = icp
    return av


def _make_event_type(
    title: str = "Consulta 30 min", duration: int = 30, slug: str = "consulta", et_id: str | None = None
) -> MagicMock:
    et = MagicMock()
    et.id = et_id or str(uuid.uuid4())
    et.title = title
    et.duration = duration
    et.slug = slug
    et.is_hidden = False
    booking = MagicMock()
    booking.max_per_day = 5
    et.booking_config = booking
    return et


def _make_testimonial(
    author: str = "María G.", role: str = "Consultora", content: str = "Excelente programa, cambia vidas."
) -> MagicMock:
    t = MagicMock()
    t.author_name = author
    t.author_role = role
    t.content = content
    t.quote = content
    t.rating = 5
    return t


def _make_authority_item(
    entity_name: str = "Forbes", item_type: str = "media", context: str = "Mencionado en Forbes MX"
) -> MagicMock:
    a = MagicMock()
    a.entity_name = entity_name
    a.type = item_type
    a.context = context
    a.title = entity_name
    return a


def _make_team_member(name: str = "Ana López", role: str = "Coach") -> MagicMock:
    m = MagicMock()
    m.id = str(uuid.uuid4())
    m.name = name
    m.role = role
    m.bio = "Especialista con 10 años de experiencia."
    m.avatar_url = None
    m.headshot_url = None
    m.display_name = name
    m.job_title = role
    return m


# ---------------------------------------------------------------------------
# Tool registry test
# ---------------------------------------------------------------------------


def test_offer_section_tools_registered() -> None:
    """All 17 tools must be in OFFER_SECTION_TOOLS."""
    assert len(OFFER_SECTION_TOOLS) == 17
    tool_names = {t.name for t in OFFER_SECTION_TOOLS}
    expected = {
        "adapt_from_brand_identity",
        "adapt_from_brand_narrative",
        "rewrite_tones",
        "validate_preset_coherence",
        "reuse_brand_buyer_personas",
        "inherit_brand_methodology",
        "high_ticket_tiering_template",
        "recurring_billing_setup",
        "detect_currency_mismatch",
        "import_scheduling_event_type",
        "detect_hybrid_split",
        "import_from_brand_vault",
        "suggest_missing_objections",
        "generate_from_preset_flags",
        "pull_sales_agent_common_questions",
        "assemble_from_brand_authority",
        "reuse_brand_team",
    }
    assert tool_names == expected


def test_offer_section_tools_in_registry_tool_groups() -> None:
    """offer_section group must exist in TOOL_GROUPS."""
    from src.modules.copilot.application.tools.registry import TOOL_GROUPS

    assert "offer_section" in TOOL_GROUPS
    assert len(TOOL_GROUPS["offer_section"]) == 17


def test_offer_studio_route_includes_offer_section() -> None:
    """offer-studio route must include offer_section group."""
    from src.modules.copilot.application.tools.registry import ROUTE_TOOL_MAP

    groups = ROUTE_TOOL_MAP.get("offer-studio", [])
    assert "offer_section" in groups


# ---------------------------------------------------------------------------
# Tool 1 — adapt_from_brand_identity
# ---------------------------------------------------------------------------


class TestAdaptFromBrandIdentity:
    def test_happy_path(self) -> None:
        settings = _make_brand_settings(identity=_make_brand_identity("Nicolify", "Crece sin límites", "entusiasta"))
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal") as mock_sl,
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
        ):
            mock_sl.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_sl.return_value.__exit__ = MagicMock(return_value=False)
            result = json.loads(adapt_from_brand_identity.invoke({}))

        assert result["section_slug"] == "identity"
        assert result["confidence"] > 0
        assert "public_name" in result["draft_fields"] or "internal_sku" in result["draft_fields"]

    def test_missing_brand(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=None),
        ):
            result = json.loads(adapt_from_brand_identity.invoke({}))

        assert result["confidence"] == 0.0
        assert result["draft_fields"] == {}
        assert len(result["suggestions"]) > 0

    def test_tenant_isolation(self) -> None:
        """_brand_settings must be called with the request-scoped tenant_id."""
        settings = _make_brand_settings()
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings
            ) as mock_bs,
        ):
            adapt_from_brand_identity.invoke({})
            mock_bs.assert_called_once()
            _, _call_kwargs = mock_bs.call_args[0], mock_bs.call_args
            # second positional arg (or first kwarg) should be TENANT_ID
            args = mock_bs.call_args[0]
            assert args[1] == TENANT_ID

    def test_prefers_personality_system_instruction_over_voice_tone(self) -> None:
        """When active personality profile exists, suggestion uses system_instruction, not voice_tone."""
        identity = _make_brand_identity("Nicolify", "Crece sin límites", "entusiasta")
        settings = _make_brand_settings(identity=identity)

        personality_profile = MagicMock()
        personality_profile.system_instruction = "BLOQUE 1 — REGLAS DE PERSONALIDAD\nCalma y precisión."

        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._active_personality",
                return_value=personality_profile,
            ),
        ):
            result = json.loads(adapt_from_brand_identity.invoke({}))

        suggestions_text = " ".join(result["suggestions"])
        # Should reference personality instruction, not the raw voice_tone string
        assert "personalidad" in suggestions_text.lower() or "estilo" in suggestions_text.lower()

    def test_falls_back_to_voice_tone_when_no_personality(self) -> None:
        """When no active personality profile, falls back to identity.voice_tone."""
        identity = _make_brand_identity("Nicolify", "Crece sin límites", "entusiasta y cálida")
        settings = _make_brand_settings(identity=identity)

        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._active_personality",
                return_value=None,
            ),
        ):
            result = json.loads(adapt_from_brand_identity.invoke({}))

        suggestions_text = " ".join(result["suggestions"])
        assert "entusiasta y cálida" in suggestions_text


# ---------------------------------------------------------------------------
# Tool 2 — adapt_from_brand_narrative
# ---------------------------------------------------------------------------


class TestAdaptFromBrandNarrative:
    def test_happy_path(self) -> None:
        narrative = _make_narrative()
        settings = _make_brand_settings(narrative=narrative)
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
        ):
            result = json.loads(adapt_from_brand_narrative.invoke({}))

        assert result["section_slug"] == "promise"
        assert result["confidence"] > 0
        assert len(result["suggestions"]) >= 1

    def test_no_narrative(self) -> None:
        settings = _make_brand_settings(narrative=None)
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
        ):
            result = json.loads(adapt_from_brand_narrative.invoke({}))

        assert result["confidence"] == 0.0
        assert result["draft_fields"] == {}

    def test_tenant_isolation(self) -> None:
        settings = _make_brand_settings(narrative=_make_narrative())
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings
            ) as mock_bs,
        ):
            adapt_from_brand_narrative.invoke({})
            args = mock_bs.call_args[0]
            assert args[1] == TENANT_ID


# ---------------------------------------------------------------------------
# Tool 3 — rewrite_tones
# ---------------------------------------------------------------------------


class TestRewriteTones:
    def test_happy_path(self) -> None:
        result = json.loads(rewrite_tones.invoke({"current_promise": "Aprende a invertir en 30 días."}))
        assert result["section_slug"] == "promise"
        assert len(result["suggestions"]) == 3
        assert any("Formal" in s for s in result["suggestions"])
        assert any("Cercano" in s or "cercano" in s for s in result["suggestions"])

    def test_empty_promise_returns_hint(self) -> None:
        result = json.loads(rewrite_tones.invoke({"current_promise": ""}))
        assert result["confidence"] == 0.0
        assert result["draft_fields"] == {}


# ---------------------------------------------------------------------------
# Tool 4 — validate_preset_coherence
# ---------------------------------------------------------------------------


class TestValidatePresetCoherence:
    def test_happy_path_no_issues(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = json.loads(
                validate_preset_coherence.invoke(
                    {"current_promise": "Transforma tu negocio con metodología premium.", "offer_id": ""}
                )
            )

        assert result["section_slug"] == "promise"
        assert result["confidence"] > 0

    def test_high_ticket_flag_missing_keywords(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["high_ticket"],
            ),
        ):
            result = json.loads(
                validate_preset_coherence.invoke({"current_promise": "Aprende algo.", "offer_id": "some-id"})
            )

        issues = result["suggestions"]
        assert any("HIGH_TICKET" in i or "premium" in i.lower() or "high_ticket" in i.lower() for i in issues)

    def test_empty_promise(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = json.loads(validate_preset_coherence.invoke({"current_promise": "", "offer_id": ""}))

        assert any("vacía" in s for s in result["suggestions"])


# ---------------------------------------------------------------------------
# Tool 5 — reuse_brand_buyer_personas
# ---------------------------------------------------------------------------


class TestReuseBrandBuyerPersonas:
    def test_happy_path(self) -> None:
        avatars = [_make_avatar("Emprendedor", True, "30-40 años, quiere escalar")]
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._avatars", return_value=avatars),
        ):
            result = json.loads(reuse_brand_buyer_personas.invoke({}))

        assert result["section_slug"] == "audience"
        assert result["confidence"] > 0
        assert "target_audience_name" in result["draft_fields"]

    def test_no_avatars(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._avatars", return_value=[]),
        ):
            result = json.loads(reuse_brand_buyer_personas.invoke({}))

        assert result["confidence"] == 0.0
        assert result["draft_fields"] == {}

    def test_tenant_isolation(self) -> None:
        avatars = [_make_avatar()]
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._avatars", return_value=avatars
            ) as mock_av,
        ):
            reuse_brand_buyer_personas.invoke({})
            args = mock_av.call_args[0]
            assert args[1] == TENANT_ID


# ---------------------------------------------------------------------------
# Tool 6 — inherit_brand_methodology
# ---------------------------------------------------------------------------


class TestInheritBrandMethodology:
    def test_happy_path(self) -> None:
        strategy = _make_strategy()
        settings = _make_brand_settings(strategy=strategy)
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
        ):
            result = json.loads(inherit_brand_methodology.invoke({}))

        assert result["section_slug"] == "methodology"
        assert result["confidence"] > 0
        assert "methodology_name" in result["draft_fields"]

    def test_no_strategy(self) -> None:
        settings = _make_brand_settings(strategy=None)
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
        ):
            result = json.loads(inherit_brand_methodology.invoke({}))

        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 7 — high_ticket_tiering_template
# ---------------------------------------------------------------------------


class TestHighTicketTieringTemplate:
    def test_happy_path_with_flag(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["high_ticket"],
            ),
        ):
            result = json.loads(high_ticket_tiering_template.invoke({"offer_id": "some-id"}))

        assert result["section_slug"] == "pricing"
        assert result["confidence"] > 0
        tiers = result["draft_fields"].get("pricing_tiers", [])
        assert len(tiers) == 3
        tier_names = [t["tier"] for t in tiers]
        assert "Básico" in tier_names
        assert "Premium" in tier_names

    def test_no_flag_returns_hint(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["recurring_billing"],
            ),
        ):
            result = json.loads(high_ticket_tiering_template.invoke({"offer_id": "some-id"}))

        assert result["confidence"] == 0.0

    def test_no_offer_id_returns_template_anyway(self) -> None:
        """Without offer_id, flags list is empty — template still returned (no flag check without ID)."""
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = json.loads(high_ticket_tiering_template.invoke({"offer_id": ""}))

        # When no offer_id, flag check is skipped → returns template
        assert "pricing_tiers" in result["draft_fields"]


# ---------------------------------------------------------------------------
# Tool 8 — recurring_billing_setup
# ---------------------------------------------------------------------------


class TestRecurringBillingSetup:
    def test_happy_path_with_flag(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["recurring_billing"],
            ),
        ):
            result = json.loads(recurring_billing_setup.invoke({"offer_id": "some-id"}))

        assert result["section_slug"] == "pricing"
        assert result["draft_fields"]["billing_cycle"] == "monthly"
        assert "trial_period_days" in result["draft_fields"]

    def test_wrong_flag_returns_hint(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["high_ticket"],
            ),
        ):
            result = json.loads(recurring_billing_setup.invoke({"offer_id": "some-id"}))

        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 9 — detect_currency_mismatch
# ---------------------------------------------------------------------------


class TestDetectCurrencyMismatch:
    def test_happy_path_no_mismatch(self) -> None:
        tenant_mock = MagicMock()
        tenant_mock.default_currency = "PEN"
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal") as mock_sl,
        ):
            db_mock = MagicMock()
            db_mock.execute.return_value.scalars.return_value.first.return_value = tenant_mock
            mock_sl.return_value = db_mock
            with (
                patch("src.modules.copilot.application.tools.offer_section_tools.TenantModel", create=True),
                patch("src.modules.copilot.application.tools.offer_section_tools.select", create=True),
            ):
                # Just test that it runs without error and returns a JSON with section_slug
                result_raw = detect_currency_mismatch.invoke({"offer_id": ""})
                result = json.loads(result_raw)
        assert result["section_slug"] == "pricing"

    def test_no_tenant_id(self) -> None:
        with patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=None):
            result = json.loads(detect_currency_mismatch.invoke({"offer_id": ""}))
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 10 — import_scheduling_event_type
# ---------------------------------------------------------------------------


class TestImportSchedulingEventType:
    def test_happy_path(self) -> None:
        et = _make_event_type("Consulta 30 min", 30, "consulta-30")
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._event_types", return_value=[et]),
        ):
            result = json.loads(import_scheduling_event_type.invoke({"event_type_id": ""}))

        assert result["section_slug"] == "schedule"
        assert result["confidence"] > 0
        assert "session_duration_minutes" in result["draft_fields"]
        assert result["draft_fields"]["session_duration_minutes"] == 30

    def test_no_event_types(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._event_types", return_value=[]),
        ):
            result = json.loads(import_scheduling_event_type.invoke({"event_type_id": ""}))

        assert result["confidence"] == 0.0

    def test_specific_event_type_id_found(self) -> None:
        et_id = str(uuid.uuid4())
        et = _make_event_type("VIP 60 min", 60, "vip-60", et_id=et_id)
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._event_types", return_value=[et]),
        ):
            result = json.loads(import_scheduling_event_type.invoke({"event_type_id": et_id}))

        assert result["draft_fields"]["session_duration_minutes"] == 60

    def test_specific_event_type_id_not_found(self) -> None:
        et = _make_event_type(et_id=str(uuid.uuid4()))
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._event_types", return_value=[et]),
        ):
            result = json.loads(import_scheduling_event_type.invoke({"event_type_id": "non-existent-id"}))

        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 11 — detect_hybrid_split
# ---------------------------------------------------------------------------


class TestDetectHybridSplit:
    def test_hybrid_detected(self) -> None:
        result = json.loads(
            detect_hybrid_split.invoke({"location_data": "El programa es híbrido: online y presencial en Bogotá."})
        )
        assert result["section_slug"] == "location"
        assert result["draft_fields"]["modality"] == "hybrid"
        assert result["confidence"] > 0

    def test_no_hybrid_keywords(self) -> None:
        result = json.loads(detect_hybrid_split.invoke({"location_data": "Solo online, 100% remoto."}))
        assert result["draft_fields"] == {}
        assert result["confidence"] > 0  # not a missing-data case, just no hybrid

    def test_empty_location_data(self) -> None:
        result = json.loads(detect_hybrid_split.invoke({"location_data": ""}))
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 12 — import_from_brand_vault
# ---------------------------------------------------------------------------


class TestImportFromBrandVault:
    def test_happy_path(self) -> None:
        ts = [_make_testimonial("Ana", "Coach", "Cambió mi vida por completo.")]
        bundle = {"testimonials": ts, "authority_items": [], "team_members": []}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ),
        ):
            result = json.loads(import_from_brand_vault.invoke({}))

        assert result["section_slug"] == "testimonials"
        assert result["confidence"] > 0
        assert len(result["draft_fields"]["testimonials"]) == 1

    def test_no_testimonials(self) -> None:
        bundle = {"testimonials": [], "authority_items": [], "team_members": []}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ),
        ):
            result = json.loads(import_from_brand_vault.invoke({}))

        assert result["confidence"] == 0.0

    def test_tenant_isolation(self) -> None:
        ts = [_make_testimonial()]
        bundle = {"testimonials": ts, "authority_items": [], "team_members": []}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ) as mock_sp,
        ):
            import_from_brand_vault.invoke({})
            args = mock_sp.call_args[0]
            assert args[1] == TENANT_ID


# ---------------------------------------------------------------------------
# Tool 13 — suggest_missing_objections
# ---------------------------------------------------------------------------


class TestSuggestMissingObjections:
    def test_happy_path_finds_missing(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = json.loads(suggest_missing_objections.invoke({"offer_id": "", "existing_objections": ""}))

        assert result["section_slug"] == "testimonials"
        # Should suggest objections since nothing is covered
        assert len(result["suggestions"]) > 1

    def test_all_covered_returns_ok(self) -> None:
        covered = "tiempo precio experiencia_previa resultados_reales soporte inversion_alta compromiso_mensual valor_gratuito"
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = json.loads(suggest_missing_objections.invoke({"offer_id": "", "existing_objections": covered}))

        assert result["confidence"] > 0.8

    def test_no_tenant_id(self) -> None:
        with patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=None):
            result = json.loads(suggest_missing_objections.invoke({"offer_id": "", "existing_objections": ""}))
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 14 — generate_from_preset_flags
# ---------------------------------------------------------------------------


class TestGenerateFromPresetFlags:
    def test_happy_path_with_flags(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["high_ticket", "recurring_billing"],
            ),
        ):
            result = json.loads(generate_from_preset_flags.invoke({"offer_id": "some-id"}))

        assert result["section_slug"] == "faq"
        faqs = result["draft_fields"]["faqs"]
        assert len(faqs) >= 5
        assert all("q" in faq and "a" in faq for faq in faqs)

    def test_no_offer_id_returns_base_faqs(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = json.loads(generate_from_preset_flags.invoke({"offer_id": ""}))

        faqs = result["draft_fields"]["faqs"]
        assert len(faqs) == 5  # only base FAQs

    def test_no_tenant_id(self) -> None:
        with patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=None):
            result = json.loads(generate_from_preset_flags.invoke({"offer_id": ""}))
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 15 — pull_sales_agent_common_questions
# ---------------------------------------------------------------------------


class TestPullSalesAgentCommonQuestions:
    def test_happy_path(self) -> None:
        row1 = MagicMock()
        row1.get = lambda k, d=None: (
            "El lead preguntó sobre el precio y la duración del programa." if k == "conversation_summary" else d
        )
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal") as mock_sl,
        ):
            db_mock = MagicMock()
            db_mock.execute.return_value.mappings.return_value.all.return_value = [row1]
            mock_sl.return_value = db_mock
            result = json.loads(pull_sales_agent_common_questions.invoke({}))

        assert result["section_slug"] == "faq"
        # May or may not extract depending on heuristic, but no exception

    def test_no_conversations(self) -> None:
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal") as mock_sl,
        ):
            db_mock = MagicMock()
            db_mock.execute.return_value.mappings.return_value.all.return_value = []
            mock_sl.return_value = db_mock
            result = json.loads(pull_sales_agent_common_questions.invoke({}))

        assert result["confidence"] == 0.0

    def test_no_tenant_id(self) -> None:
        with patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=None):
            result = json.loads(pull_sales_agent_common_questions.invoke({}))
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Tool 16 — assemble_from_brand_authority
# ---------------------------------------------------------------------------


class TestAssembleFromBrandAuthority:
    def test_happy_path(self) -> None:
        ai = _make_authority_item("Forbes", "media", "Mención en Forbes MX 2024")
        bundle = {"testimonials": [], "authority_items": [ai], "team_members": []}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ),
        ):
            result = json.loads(assemble_from_brand_authority.invoke({}))

        assert result["section_slug"] == "value_stack"
        assert result["confidence"] > 0
        assert len(result["draft_fields"]["value_stack"]) == 1

    def test_no_authority_items(self) -> None:
        bundle = {"testimonials": [], "authority_items": [], "team_members": []}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ),
        ):
            result = json.loads(assemble_from_brand_authority.invoke({}))

        assert result["confidence"] == 0.0

    def test_tenant_isolation(self) -> None:
        ai = _make_authority_item()
        bundle = {"testimonials": [], "authority_items": [ai], "team_members": []}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ) as mock_sp,
        ):
            assemble_from_brand_authority.invoke({})
            args = mock_sp.call_args[0]
            assert args[1] == TENANT_ID


# ---------------------------------------------------------------------------
# Tool 17 — reuse_brand_team
# ---------------------------------------------------------------------------


class TestReuseBrandTeam:
    def test_happy_path_from_social_proof(self) -> None:
        tm = _make_team_member("Ana López", "Coach")
        bundle = {"testimonials": [], "authority_items": [], "team_members": [tm]}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._brand_settings",
                return_value=_make_brand_settings(),
            ),
        ):
            result = json.loads(reuse_brand_team.invoke({}))

        assert result["section_slug"] == "instructors"
        assert result["confidence"] > 0
        instructors = result["draft_fields"]["instructors"]
        assert len(instructors) >= 1
        assert instructors[0]["name"] == "Ana López"

    def test_no_team_members(self) -> None:
        bundle = {"testimonials": [], "authority_items": [], "team_members": []}
        settings = _make_brand_settings(team=[])
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ),
            patch("src.modules.copilot.application.tools.offer_section_tools._brand_settings", return_value=settings),
        ):
            result = json.loads(reuse_brand_team.invoke({}))

        assert result["confidence"] == 0.0

    def test_tenant_isolation(self) -> None:
        tm = _make_team_member()
        bundle = {"testimonials": [], "authority_items": [], "team_members": [tm]}
        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=TENANT_ID),
            patch("src.modules.copilot.application.tools.offer_section_tools.SessionLocal"),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._social_proof_bundle", return_value=bundle
            ) as mock_sp,
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._brand_settings",
                return_value=_make_brand_settings(),
            ),
        ):
            reuse_brand_team.invoke({})
            args = mock_sp.call_args[0]
            assert args[1] == TENANT_ID
