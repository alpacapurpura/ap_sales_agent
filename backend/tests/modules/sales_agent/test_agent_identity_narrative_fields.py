"""Tests for narrative field rendering in agent_identity.j2.

CONTRACT §12.2 (Fase 7): los 13 narrative fields del Offer deben renderizarse
de forma defensiva en el template del agente.

Covers:
1. Offer con todos los campos narrativos poblados → cada sección aparece.
2. Offer sin ningún campo narrativo → template no falla + no deja secciones vacías.
3. Objeciones con trigger_phrases → las frases se muestran en el template.
4. Offer con sólo un subconjunto de campos → solo esas secciones aparecen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = str(
    Path(__file__).parent
    / ".."
    / ".."
    / ".."
    / "src"
    / "modules"
    / "sales_agent"
    / "infrastructure"
    / "prompts"
    / "templates",
)


@pytest.fixture
def jinja_env() -> Environment:
    """Jinja environment pointing at the real templates directory."""
    return Environment(
        loader=FileSystemLoader(str(Path(TEMPLATES_DIR).resolve())),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _base_context(**offer_overrides: Any) -> dict[str, Any]:
    """Minimal context with one offer dict. offer_overrides merge into the offer."""
    offer: dict[str, Any] = {
        "public_name": "Curso de Marketing Digital",
        "headline_promise": "Triplica tus ventas en 90 días",
        "primary_outcome": None,
        "time_to_value": None,
        "preset_label": None,
        "preset_description": None,
        "preset_flags": [],
        "archetype": "programa",
        "format_hint": None,
        "type": "programa",
        "pricing_options": [],
        "guarantee_type": None,
        "guarantee_terms": None,
        "deliverables": [],
        "marketing_pain_points": [],
        "marketing_desires": [],
        "objections": [],
        "checkout_page_url": None,
        "calendar_type_id": None,
        # Narrative fields (todas en None/[] por defecto)
        "before_state": None,
        "after_state": None,
        "why_now": None,
        "measurable_outcomes": [],
        "cultural_trust_barriers": [],
        "emotional_triggers": [],
        "status_drivers": [],
        "regret_scenarios": [],
        "urgency_drivers": [],
        "scarcity_reason_honest": None,
        "refund_process_description": None,
        "bonus_if_act_now": None,
        "final_push_copy": None,
    }
    offer.update(offer_overrides)
    return {
        "has_brand": True,
        "identity": {"brand_name": "AcademiaPro"},
        "strategy": {},
        "story": {},
        "team": [],
        "contact": {},
        "positioning": {},
        "testimonials": [],
        "authority_items": [],
        "default_avatar": {},
        "avatars": [],
        "offers": [offer],
        "has_team": False,
        "has_avatars": False,
        "has_offers": True,
        "has_testimonials": False,
        "has_authority": False,
        "personality_instruction": None,
        "has_legal_guardrails": False,
        "has_regulated_profession": False,
        "has_legal_documents": False,
        "channel_type": "whatsapp",
    }


class TestNarrativeFieldsPopulated:
    """Template renders correctly when all 13 narrative fields are present."""

    @pytest.fixture
    def rendered(self, jinja_env: Environment) -> str:
        ctx = _base_context(
            before_state="El cliente pasa horas en redes sin ver resultados concretos.",
            after_state="Genera sus primeras ventas automatizadas en menos de 30 días.",
            why_now="Cada mes sin sistema cuesta clientes que van a la competencia.",
            measurable_outcomes=[
                "3x ROAS en el primer mes",
                "50% reducción de tiempo operativo",
            ],
            cultural_trust_barriers=[
                "Desconfianza a pagar online con tarjeta internacional",
                "Preferencia por WhatsApp antes de dar datos de pago",
            ],
            emotional_triggers=[
                "Miedo a quedarse atrás mientras otros escalan",
                "Deseo de dejar de depender de clientes uno a uno",
            ],
            status_drivers=[
                "Ser reconocido como referente del sector",
                "Poder decir que tiene un negocio escalable",
            ],
            regret_scenarios=[
                "En 6 meses sigue cobrando lo mismo y saturado de llamadas",
                "Un colega lanza el mismo curso antes y se lleva el mercado",
            ],
            urgency_drivers=[
                "El grupo arranca en 10 días y cierra el acceso",
                "El precio sube 30% en la siguiente edición",
            ],
            scarcity_reason_honest="Cupo limitado a 20 personas por capacidad de mentoría en vivo.",
            refund_process_description=(
                "Si en 30 días no estás satisfecho, devolvemos el 100% por la misma vía de pago. "
                "Transferencia: 3–5 días hábiles. Tarjeta: hasta 10 días según el banco."
            ),
            bonus_if_act_now="Sesión de auditoría 1:1 de 60 minutos si te inscribes antes del viernes.",
            final_push_copy=(
                "Llevas meses buscando la forma de escalar. Este es el momento. "
                "Tenemos garantía de devolución — no hay riesgo real. ¿Te apunto?"
            ),
        )
        return jinja_env.get_template("agent_identity.j2").render(**ctx)

    def test_before_state_renders(self, rendered: str) -> None:
        assert "pasa horas en redes sin ver resultados" in rendered

    def test_after_state_renders(self, rendered: str) -> None:
        assert "primeras ventas automatizadas" in rendered

    def test_why_now_renders(self, rendered: str) -> None:
        assert "Cada mes sin sistema cuesta clientes" in rendered

    def test_measurable_outcomes_renders(self, rendered: str) -> None:
        assert "3x ROAS en el primer mes" in rendered
        assert "50% reducción de tiempo operativo" in rendered

    def test_cultural_trust_barriers_renders(self, rendered: str) -> None:
        assert "Desconfianza a pagar online" in rendered
        assert "Preferencia por WhatsApp" in rendered

    def test_emotional_triggers_renders(self, rendered: str) -> None:
        assert "Miedo a quedarse atrás" in rendered
        assert "Deseo de dejar de depender" in rendered

    def test_status_drivers_renders(self, rendered: str) -> None:
        assert "Ser reconocido como referente" in rendered

    def test_regret_scenarios_renders(self, rendered: str) -> None:
        assert "En 6 meses sigue cobrando lo mismo" in rendered

    def test_urgency_drivers_renders(self, rendered: str) -> None:
        assert "El grupo arranca en 10 días" in rendered

    def test_scarcity_reason_renders(self, rendered: str) -> None:
        assert "20 personas por capacidad de mentoría" in rendered

    def test_refund_process_renders(self, rendered: str) -> None:
        assert "devolvemos el 100%" in rendered

    def test_bonus_if_act_now_renders(self, rendered: str) -> None:
        assert "auditoría 1:1 de 60 minutos" in rendered

    def test_final_push_copy_renders(self, rendered: str) -> None:
        assert "Llevas meses buscando la forma de escalar" in rendered


class TestNarrativeFieldsEmpty:
    """Template does not fail and does not emit empty section headers when fields are absent."""

    @pytest.fixture
    def rendered(self, jinja_env: Environment) -> str:
        """All narrative fields at their defaults (None / [])."""
        ctx = _base_context()
        return jinja_env.get_template("agent_identity.j2").render(**ctx)

    def test_template_renders_without_error(self, rendered: str) -> None:
        assert "AcademiaPro" in rendered

    def test_no_before_state_section(self, rendered: str) -> None:
        assert "Situación previa típica" not in rendered

    def test_no_after_state_section(self, rendered: str) -> None:
        assert "Situación objetivo" not in rendered

    def test_no_why_now_section(self, rendered: str) -> None:
        assert "Por qué actuar ahora" not in rendered

    def test_no_measurable_outcomes_section(self, rendered: str) -> None:
        assert "Resultados medibles" not in rendered

    def test_no_cultural_barriers_section(self, rendered: str) -> None:
        assert "Barreras culturales Latam" not in rendered

    def test_no_emotional_triggers_section(self, rendered: str) -> None:
        assert "Disparadores emocionales" not in rendered

    def test_no_status_drivers_section(self, rendered: str) -> None:
        assert "Motores de estatus" not in rendered

    def test_no_regret_scenarios_section(self, rendered: str) -> None:
        assert "Escenarios de arrepentimiento" not in rendered

    def test_no_urgency_drivers_section(self, rendered: str) -> None:
        assert "Urgencia honesta" not in rendered

    def test_no_scarcity_section(self, rendered: str) -> None:
        assert "Motivo de escasez real" not in rendered

    def test_no_refund_process_section(self, rendered: str) -> None:
        assert "Proceso de devolución" not in rendered

    def test_no_bonus_section(self, rendered: str) -> None:
        assert "Bonus por decidir ahora" not in rendered

    def test_no_final_push_section(self, rendered: str) -> None:
        assert "Cierre sugerido" not in rendered


class TestObjectionsWithTriggerPhrases:
    """Objections with trigger_phrases expose the phrases in the rendered template."""

    def test_trigger_phrases_appear_in_template(self, jinja_env: Environment) -> None:
        ctx = _base_context(
            objections=[
                {
                    "type": "price",
                    "rebuttal": "Entiendo la preocupación. El curso se paga con la primera venta.",
                    "strategy": "ROI Reframing",
                    "trigger_phrases": ["Está muy caro", "No tengo presupuesto"],
                }
            ]
        )
        rendered = jinja_env.get_template("agent_identity.j2").render(**ctx)
        assert "Está muy caro" in rendered
        assert "No tengo presupuesto" in rendered
        assert "ROI Reframing" in rendered
        assert "Entiendo la preocupación" in rendered

    def test_objection_without_trigger_phrases_renders_gracefully(self, jinja_env: Environment) -> None:
        ctx = _base_context(
            objections=[
                {
                    "type": "trust",
                    "rebuttal": "Tenemos garantía de 30 días sin preguntas.",
                    "strategy": "Risk Reversal + Guarantee",
                    "trigger_phrases": [],
                }
            ]
        )
        rendered = jinja_env.get_template("agent_identity.j2").render(**ctx)
        assert "Tenemos garantía de 30 días" in rendered
        # No empty "Frases del lead:" line should appear
        assert "Frases del lead:  " not in rendered


class TestPartialNarrativeFields:
    """When only a subset of narrative fields is set, only those sections appear."""

    def test_only_before_after_state_renders(self, jinja_env: Environment) -> None:
        ctx = _base_context(
            before_state="Sin sistema de ventas claro.",
            after_state="Con proceso automatizado de captación.",
        )
        rendered = jinja_env.get_template("agent_identity.j2").render(**ctx)
        assert "Situación previa típica" in rendered
        assert "Situación objetivo" in rendered
        # Fields not set must not appear
        assert "Urgencia honesta" not in rendered
        assert "Proceso de devolución" not in rendered

    def test_only_closing_fields_render(self, jinja_env: Environment) -> None:
        ctx = _base_context(
            urgency_drivers=["Precio sube en 48 horas"],
            final_push_copy="Es el momento — ¿te apunto?",
        )
        rendered = jinja_env.get_template("agent_identity.j2").render(**ctx)
        assert "Urgencia honesta" in rendered
        assert "Precio sube en 48 horas" in rendered
        assert "Cierre sugerido" in rendered
        assert "Es el momento" in rendered
        # Promise fields must not appear
        assert "Situación previa típica" not in rendered
        assert "Resultados medibles" not in rendered
