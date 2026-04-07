"""Tests for sales_agent prompt template rendering.

Validates that all Jinja2 templates render without errors and produce
expected structural elements (output format blocks, framework references,
channel-specific formatting, new humanization rules).
"""

import os

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "src",
    "modules",
    "sales_agent",
    "infrastructure",
    "prompts",
    "templates",
)


@pytest.fixture
def jinja_env():
    return Environment(
        loader=FileSystemLoader(os.path.abspath(TEMPLATES_DIR)),
        autoescape=False,  # noqa: S701 — Jinja templates are server-side prompts, not HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )


# ── Minimal context dicts for each template ───────────────────

MINIMAL_CONTEXT = {
    "channel_type": "instagram",
    "lead_score": 0,
    "turn_count": 0,
    "qualification_answers": None,
    "buying_signals": [],
    "objection_history": [],
    "close_strategy": None,
    "active_product": None,
    "context_rag": None,
}

SUPERVISOR_CONTEXT = {
    "intent": "unknown",
    "lead_score": 0,
    "stage": "awareness",
    "buying_signals_count": 0,
    "objection_count": 0,
    "qualification_completeness": 0,
    "last_specialist": "none",
    "turn_count": 0,
    "lead_data": None,
    "user_profile": None,
}

IDENTITY_CONTEXT = {
    "has_brand": True,
    "identity": {
        "brand_name": "TestBrand",
        "tagline": "We test things",
        "voice_tone": "Professional",
        "communication_style": "Friendly",
    },
    "strategy": {"mission": "Test mission"},
    "positioning": {"unique_value_proposition": "Best tests"},
    "story": None,
    "has_team": False,
    "team": [],
    "has_avatars": True,
    "default_avatar": {
        "name": "Test Avatar",
        "icp_description": "Testers who test",
        "anti_avatar": "People who don't test",
    },
    "avatars": [],
    "has_offers": True,
    "offers": [
        {
            "public_name": "Test Offer",
            "archetype": "course",
            "format_hint": "online",
            "type": "digital",
            "headline_promise": "You will learn testing",
            "primary_outcome": "Master testing",
            "time_to_value": "4 weeks",
            "pricing_options": [
                {
                    "label": "Full",
                    "total_amount": 299,
                    "number_of_installments": 1,
                    "installment_amount": 299,
                },
            ],
            "currency": "USD",
            "guarantee_type": "money_back",
            "guarantee_terms": "30 days",
            "deliverables": [
                {"name": "Video Course", "format": "video", "quantity": 10},
            ],
            "marketing_pain_points": ["lack of confidence"],
            "marketing_desires": ["career growth"],
            "objections": [
                {
                    "type": "price",
                    "strategy": "ROI Reframing",
                    "rebuttal": "Think of the ROI",
                },
            ],
            "checkout_page_url": "https://pay.example.com/test",
            "calendar_type_id": "cal_123",
        }
    ],
    "has_testimonials": True,
    "testimonials": [
        {"quote": "Great product!", "author": "Jane", "role": "CEO"},
    ],
    "channel_type": "instagram",
}


# ── Each template renders without Jinja2 errors ──────────────


class TestTemplateRendering:
    """Every template must render with minimal context without raising."""

    def test_humanization_rules_renders(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "REGLAS DE HUMANIZACIÓN" in result

    def test_buying_signals_renders(self, jinja_env):
        template = jinja_env.get_template("buying_signals.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Detección de Señales" in result

    def test_specialist_qualifier_renders(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Qualifier" in result

    def test_specialist_closer_renders(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Closer" in result

    def test_specialist_product_expert_renders(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Product Expert" in result

    def test_supervisor_routing_renders(self, jinja_env):
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**SUPERVISOR_CONTEXT)
        assert "Sales Supervisor" in result

    def test_agent_identity_renders(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "TestBrand" in result


# ── Humanization rules: new anti-verbosity rules ─────────────


class TestHumanizationNewRules:
    """humanization_rules.j2 contains new anti-verbosity and behavioral rules."""

    def test_cap_absoluto(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "NUNCA más de 5 líneas" in result

    def test_piramide_invertida(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Pirámide invertida" in result

    def test_hook_obligatorio(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "HOOK OBLIGATORIO" in result

    def test_espejeo_de_longitud(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "ESPEJEO DE LONGITUD" in result

    def test_anti_patrones_with_examples(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "MAL:" in result
        assert "BIEN:" in result


# ── Greeting protocol per time range ─────────────────────────


class TestGreetingProtocol:
    """humanization_rules.j2 renders correct greeting protocol per session gap."""

    def test_no_greeting_under_6h(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "session_gap_hours": 2.0,
            "last_session_summary": None,
        }
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**ctx)
        assert "NO saludes" in result

    def test_brief_greeting_6_to_24h(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "session_gap_hours": 12.0,
            "last_session_summary": None,
        }
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**ctx)
        assert "Hola de nuevo" in result

    def test_warm_greeting_1_to_7_days(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "session_gap_hours": 72.0,
            "last_session_summary": None,
        }
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**ctx)
        assert "cálido" in result.lower() or "en qué quedaron" in result

    def test_full_recontact_over_7_days(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "session_gap_hours": 200.0,
            "last_session_summary": None,
        }
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**ctx)
        assert "Re-contacto" in result

    def test_session_summary_injected(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "session_gap_hours": 48.0,
            "last_session_summary": "Maria interested in course, objected on price",
        }
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**ctx)
        assert "Maria interested in course" in result

    def test_no_protocol_without_gap(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Protocolo de Saludo" not in result


# ── Channel-specific blocks ──────────────────────────────────


class TestHumanizationChannelBlocks:
    @pytest.mark.parametrize(
        "channel,expected_fragment",
        [
            ("instagram", "ultra cortos"),
            ("whatsapp", "cálido y cercano"),
            ("telegram", "negritas"),
            ("web", "profesional y cercano"),
        ],
    )
    def test_channel_type_block(self, jinja_env, channel, expected_fragment):
        template = jinja_env.get_template("agent_identity.j2")
        ctx = {**IDENTITY_CONTEXT, "channel_type": channel}
        result = template.render(**ctx)
        assert expected_fragment in result


# ── Buying signals ───────────────────────────────────────────


class TestBuyingSignals:
    def test_contains_signal_format(self, jinja_env):
        template = jinja_env.get_template("buying_signals.j2")
        result = template.render()
        assert "[SIGNALS:" in result
        assert '"buying"' in result
        assert '"objections"' in result

    def test_contains_explicit_signals(self, jinja_env):
        template = jinja_env.get_template("buying_signals.j2")
        result = template.render()
        assert "Señales de Compra Explícitas" in result

    def test_contains_implicit_signals(self, jinja_env):
        template = jinja_env.get_template("buying_signals.j2")
        result = template.render()
        assert "Señales de Compra Implícitas" in result


# ── Qualifier: new rules ─────────────────────────────────────


class TestQualifierOutput:
    def test_qualification_data_block(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "[QUALIFICATION_DATA:" in result

    def test_spin_framework_reference(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "SPIN" in result
        assert "Situación" in result
        assert "Problema" in result
        assert "Implicación" in result
        assert "Necesidad-Beneficio" in result

    def test_includes_humanization(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "REGLAS DE HUMANIZACIÓN" in result

    def test_includes_buying_signals(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Detección de Señales" in result

    def test_shows_qualification_answers_when_present(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "qualification_answers": {"name": "Ana", "business_type": "coaching"},
        }
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**ctx)
        assert "Ana" in result
        assert "coaching" in result

    def test_da_antes_de_pedir_rule(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "DA ANTES DE PEDIR" in result

    def test_sinceridad_radical(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Sinceridad Radical" in result

    def test_fatigue_alert_when_high(self, jinja_env):
        ctx = {**MINIMAL_CONTEXT, "consecutive_questions": 4}
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**ctx)
        assert "ALERTA DE FATIGA" in result

    def test_no_fatigue_alert_when_low(self, jinja_env):
        ctx = {**MINIMAL_CONTEXT, "consecutive_questions": 1}
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**ctx)
        assert "ALERTA DE FATIGA" not in result


# ── Closer: new rules ────────────────────────────────────────


class TestCloserOutput:
    def test_tool_request_block(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "[TOOL_REQUEST:" in result
        assert "send_payment_link" in result
        assert "check_schedule" in result
        assert "escalate_to_human" in result

    def test_aikido_framework(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Aikido" in result
        assert "Validar" in result
        assert "Redirigir" in result

    def test_includes_humanization(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "REGLAS DE HUMANIZACIÓN" in result

    def test_includes_buying_signals(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Detección de Señales" in result

    def test_shows_active_product(self, jinja_env):
        ctx = {**MINIMAL_CONTEXT, "active_product": {"name": "Premium Course"}}
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**ctx)
        assert "Premium Course" in result

    def test_shows_objection_history(self, jinja_env):
        ctx = {**MINIMAL_CONTEXT, "objection_history": ["price", "time"]}
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**ctx)
        assert "price" in result

    def test_regla_de_un_intento(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "UN solo rebate" in result

    def test_no_inventes_descuentos(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "NUNCA inventes descuentos" in result

    def test_relajacion_ante_no(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Relajación" in result

    def test_diferenciacion_por_ticket(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "< $100" in result
        assert "$100-$500" in result
        assert "> $500" in result
        assert "SIEMPRE agendar" in result

    def test_aikido_before_after_examples(self, jinja_env):
        template = jinja_env.get_template("specialist_closer.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "ANTES:" in result
        assert "DESPUÉS:" in result


# ── Supervisor: new rules ────────────────────────────────────


class TestSupervisorRouting:
    def test_stage_gate_closer(self, jinja_env):
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**SUPERVISOR_CONTEXT)
        assert "lead_score >= 30" in result
        assert "buying_signals >= 2" in result

    def test_escalate_option(self, jinja_env):
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**SUPERVISOR_CONTEXT)
        assert "escalate" in result
        assert "turn_count > 10" in result

    def test_renders_context_variables(self, jinja_env):
        ctx = {
            **SUPERVISOR_CONTEXT,
            "lead_score": 75,
            "turn_count": 5,
            "buying_signals_count": 3,
        }
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**ctx)
        assert "75" in result
        assert "3" in result

    def test_optional_lead_data(self, jinja_env):
        ctx = {**SUPERVISOR_CONTEXT, "lead_data": {"name": "Carlos"}}
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**ctx)
        assert "Carlos" in result

    def test_no_scheduler_option(self, jinja_env):
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**SUPERVISOR_CONTEXT)
        assert "scheduler" not in result.lower()

    def test_fatigue_alert_in_supervisor(self, jinja_env):
        ctx = {**SUPERVISOR_CONTEXT, "consecutive_questions": 4}
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**ctx)
        assert "FATIGUE ALERT" in result

    def test_session_gap_long_absence(self, jinja_env):
        ctx = {**SUPERVISOR_CONTEXT, "session_gap_hours": 200.0}
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**ctx)
        assert "qualifier" in result.lower()


# ── Agent identity: new voice examples ───────────────────────


class TestAgentIdentityVoice:
    def test_voice_examples_with_brand(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "Tu Voz (Ejemplos de Concisión)" in result

    def test_nunca_digas_section(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "NUNCA Digas" in result
        assert "Soy el asistente de" in result

    def test_no_voice_without_brand(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "identity": {}, "has_brand": False}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "Tu Voz (Ejemplos de Concisión)" not in result

    def test_channel_rules_instagram(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "channel_type": "instagram"}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "ultra cortos" in result

    def test_security_rules_still_present(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "Reglas de Seguridad" in result
        assert "NUNCA inventes información" in result


# ── Product Expert: new rules ────────────────────────────────


class TestProductExpert:
    def test_consultative_approach(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Consultivo" in result

    def test_signal_detection(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "[SIGNALS:" in result

    def test_rag_context_when_present(self, jinja_env):
        ctx = {
            **MINIMAL_CONTEXT,
            "context_rag": "Additional knowledge about the product",
        }
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**ctx)
        assert "Additional knowledge about the product" in result

    def test_no_rag_section_when_absent(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Knowledge Base" not in result

    def test_piramide_invertida(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Pirámide Invertida" in result

    def test_regla_no_datos(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "confirmarte ese dato con el equipo" in result

    def test_includes_buying_signals(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Detección de Señales" in result
