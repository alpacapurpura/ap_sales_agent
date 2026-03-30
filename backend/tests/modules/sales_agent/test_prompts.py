"""Tests for sales_agent prompt template rendering.

Validates that all Jinja2 templates render without errors and produce
expected structural elements (output format blocks, framework references,
channel-specific formatting).
"""

import os

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "src", "modules", "sales_agent",
    "infrastructure", "prompts", "templates",
)


@pytest.fixture
def jinja_env():
    return Environment(
        loader=FileSystemLoader(os.path.abspath(TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


# ── Minimal context dicts for each template ───────────────────────

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
    "identity": {"brand_name": "TestBrand", "tagline": "We test things", "voice_tone": "Professional", "communication_style": "Friendly"},
    "strategy": {"mission": "Test mission"},
    "positioning": {"unique_value_proposition": "Best tests"},
    "story": None,
    "has_team": False,
    "team": [],
    "has_avatars": True,
    "default_avatar": {"name": "Test Avatar", "icp_description": "Testers who test", "anti_avatar": "People who don't test"},
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
                {"label": "Full", "total_amount": 299, "number_of_installments": 1, "installment_amount": 299},
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
                {"type": "price", "strategy": "ROI Reframing", "rebuttal": "Think of the ROI"},
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


# ── Task 4.8.1: Each template renders without Jinja2 errors ──────


class TestTemplateRendering:
    """Every template must render with minimal context without raising."""

    def test_humanization_rules_renders(self, jinja_env):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Reglas de Humanización" in result

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


# ── Task 4.8.2: Channel-specific blocks in humanization_rules ────


class TestHumanizationChannelBlocks:
    """humanization_rules.j2 renders channel-specific formatting for each type."""

    @pytest.mark.parametrize(
        "channel,expected_fragment",
        [
            ("instagram", "ultra cortos"),
            ("whatsapp", "cálido y cercano"),
            ("telegram", "negritas"),
            ("web", "profesional y cercano"),  # fallback
        ],
    )
    def test_channel_type_block(self, jinja_env, channel, expected_fragment):
        template = jinja_env.get_template("humanization_rules.j2")
        result = template.render(channel_type=channel)
        assert expected_fragment in result


# ── Task 4.8.3: Buying signals format instructions ───────────────


class TestBuyingSignals:
    """buying_signals.j2 includes the signal output format."""

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


# ── Task 4.8.4: Qualifier includes QUALIFICATION_DATA format ─────


class TestQualifierOutput:
    """specialist_qualifier.j2 includes data output instructions."""

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
        assert "Reglas de Humanización" in result

    def test_includes_buying_signals(self, jinja_env):
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Detección de Señales" in result

    def test_shows_qualification_answers_when_present(self, jinja_env):
        ctx = {**MINIMAL_CONTEXT, "qualification_answers": {"name": "Ana", "business_type": "coaching"}}
        template = jinja_env.get_template("specialist_qualifier.j2")
        result = template.render(**ctx)
        assert "Ana" in result
        assert "coaching" in result


# ── Task 4.8.5: Closer includes TOOL_REQUEST instructions ────────


class TestCloserOutput:
    """specialist_closer.j2 includes tool request and Aikido framework."""

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
        assert "Reglas de Humanización" in result

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


# ── Task 4.8.6: Supervisor includes stage gates ──────────────────


class TestSupervisorRouting:
    """supervisor_routing.j2 includes decision rules with score gates."""

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
        ctx = {**SUPERVISOR_CONTEXT, "lead_score": 75, "turn_count": 5, "buying_signals_count": 3}
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**ctx)
        assert "75" in result
        assert "3" in result  # buying_signals_count

    def test_optional_lead_data(self, jinja_env):
        ctx = {**SUPERVISOR_CONTEXT, "lead_data": {"name": "Carlos"}}
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**ctx)
        assert "Carlos" in result

    def test_no_scheduler_option(self, jinja_env):
        """Scheduler was replaced by escalate in the new routing."""
        template = jinja_env.get_template("supervisor_routing.j2")
        result = template.render(**SUPERVISOR_CONTEXT)
        assert "scheduler" not in result.lower()


# ── Task 4.8.7: Agent identity voice examples with brand data ────


class TestAgentIdentityVoice:
    """agent_identity.j2 renders voice examples when brand data is present."""

    def test_voice_examples_with_brand(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "Voz y Tono (Ejemplos)" in result
        assert "asistente de TestBrand" in result

    def test_voice_uses_avatar_name(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "Test Avatar" in result

    def test_no_voice_without_brand(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "identity": {}, "has_brand": False}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "Voz y Tono (Ejemplos)" not in result

    def test_channel_rules_instagram(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "channel_type": "instagram"}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "ultra cortos" in result

    def test_channel_rules_whatsapp(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "channel_type": "whatsapp"}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "cálido y cercano" in result

    def test_channel_rules_telegram(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "channel_type": "telegram"}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "negritas" in result

    def test_channel_rules_fallback(self, jinja_env):
        ctx = {**IDENTITY_CONTEXT, "channel_type": "web"}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)
        assert "profesional y cercano" in result

    def test_security_rules_still_present(self, jinja_env):
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**IDENTITY_CONTEXT)
        assert "Reglas de Seguridad" in result
        assert "NUNCA inventes información" in result


# ── Product Expert basic checks ──────────────────────────────────


class TestProductExpert:
    """specialist_product_expert.j2 includes consultative approach."""

    def test_consultative_approach(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Consultivo" in result

    def test_signal_detection(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "[SIGNALS:" in result

    def test_rag_context_when_present(self, jinja_env):
        ctx = {**MINIMAL_CONTEXT, "context_rag": "Additional knowledge about the product"}
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**ctx)
        assert "Additional knowledge about the product" in result

    def test_no_rag_section_when_absent(self, jinja_env):
        template = jinja_env.get_template("specialist_product_expert.j2")
        result = template.render(**MINIMAL_CONTEXT)
        assert "Knowledge Base" not in result
