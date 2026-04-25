"""Golden snapshot for ``agent_identity.j2`` offer-block rendering.

Locks byte-identical output for a synthetic offer covering every field
the template currently surfaces. Future refactors (Fase 05+) must keep
this file green to prove UX (the agent prompt) didn't drift.

Refresh: when an *intentional* template change ships, regenerate via
the helper at the bottom of this file (``REFRESH_GOLDEN=1``) and audit
the diff in the PR.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = (
    Path(__file__).parent
    / ".."
    / ".."
    / ".."
    / "src"
    / "modules"
    / "sales_agent"
    / "infrastructure"
    / "prompts"
    / "templates"
).resolve()

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "agent_identity_offer_golden.txt"


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _full_offer() -> dict[str, Any]:
    """Synthetic offer covering every renderable field in agent_identity.j2."""
    return {
        "public_name": "Programa Alquimia LATAM",
        "preset_label": "Coach bootcamp 12 semanas",
        "preset_description": "Programa cohort-based con mentoría 1:1 y comunidad activa.",
        "preset_flags": ["IS_LEAD_MAGNET", "HIGH_TICKET", "RECURRING_BILLING"],
        "archetype": "programa",
        "format_hint": "cohorte",
        "type": "programa",
        "headline_promise": "Pasa de freelance reactivo a estudio rentable en 90 días",
        "primary_outcome": "Pipeline de clientes premium recurrente",
        "time_to_value": "primer cliente premium en 4 semanas",
        "pricing_options": [
            {
                "label": "Pago único",
                "total_amount": 1497,
                "number_of_installments": 1,
                "installment_amount": 1497,
            },
            {
                "label": "3 cuotas",
                "total_amount": 1797,
                "number_of_installments": 3,
                "installment_amount": 599,
            },
        ],
        "currency": "USD",
        "tax_included": True,
        "installments_available": "3, 6, 12",
        "accepted_payment_providers": ["mercadopago", "stripe"],
        "guarantee_type": "money_back",
        "guarantee_terms": "Devolución completa hasta el día 14, sin preguntas.",
        "deliverables": [
            {"name": "12 sesiones grupales en vivo", "format": "live", "quantity": 12},
            {"name": "Plantillas y SOPs operativos", "format": "pdf", "quantity": 18},
            {"name": "Mentoría 1:1 mensual", "format": "live", "quantity": 3},
        ],
        "marketing_pain_points": [
            "Cobro por hora y techo de ingresos",
            "Sin previsibilidad de pipeline",
            "Tareas operativas comen el tiempo creativo",
        ],
        "marketing_desires": [
            "Ingreso recurrente >USD 8k/mes",
            "Ser referente regional del nicho",
            "Liberarse de la operación diaria",
        ],
        "objections": [
            {
                "type": "precio",
                "strategy": "valor",
                "rebuttal": "El programa se paga solo con el primer cliente premium.",
                "trigger_phrases": ["caro", "no me alcanza", "es mucha plata"],
            },
            {
                "type": "tiempo",
                "strategy": "ROI",
                "rebuttal": "Son 4-6 horas semanales y el sistema queda activado para siempre.",
                "trigger_phrases": ["no tengo tiempo", "mucha demanda"],
            },
        ],
        "before_state": "Trabajás 60 horas semanales atendiendo clientes que regatean precio.",
        "after_state": "Atendés solo clientes premium que valoran tu criterio.",
        "why_now": "Cada mes que postergás es un cliente premium que tu competencia capta.",
        "measurable_outcomes": [
            "Ticket promedio +250%",
            "Margen operativo +40 pp",
            "Tiempo facturable -50%",
        ],
        "cultural_trust_barriers": [
            "Desconfianza Latam ante prepagos altos",
            "Miedo a programas USA que ignoran realidad regional",
        ],
        "emotional_triggers": ["miedo al techo", "deseo de reconocimiento"],
        "status_drivers": ["estudio reconocido", "speaker en eventos del nicho"],
        "regret_scenarios": [
            "Dentro de 12 meses seguir cobrando lo mismo y rechazando proyectos por falta de equipo.",
            "Ver competidores menos talentosos posicionarse como referentes regionales.",
        ],
        "urgency_drivers": [
            "Cohorte cierra el viernes 30",
            "Bonus mentoría adicional para los primeros 5 inscriptos",
        ],
        "scarcity_reason_honest": "Solo 12 plazas para mantener calidad de mentoría 1:1.",
        "refund_process_description": "Email a soporte → reembolso 100% por el mismo medio en 5 días hábiles.",
        "bonus_if_act_now": "Sesión privada de auditoría de pricing con el director.",
        "final_push_copy": "Listo. ¿Vas con pago único o cuotas?",
        "checkout_page_url": "https://pago.alquimia.lat/programa",
        "calendar_type_id": "calendly-asesoria",
    }


def _base_context() -> dict[str, Any]:
    """Brand-side context kept stable; only the offers loop is exercised."""
    return {
        "has_brand": True,
        "identity": {
            "brand_name": "Alquimia LATAM",
            "tagline": "Estudios creativos premium para Latam.",
            "voice_tone": "Cálido, directo, con vocabulario regional neutro.",
            "communication_style": "Tutea siempre. Cero spanglish gratuito.",
        },
        "strategy": {"mission": "Hacer que el talento Latam cobre lo que vale."},
        "story": {},
        "team": [],
        "contact": {},
        "positioning": {"unique_value_proposition": "El único bootcamp pricing-first del mercado regional."},
        "testimonials": [],
        "authority_items": [],
        "default_avatar": {
            "name": "Director creativo Latam",
            "icp_description": "Freelance senior con 5+ años de cartera regional.",
            "anti_avatar": "Estudiante recién graduado sin cartera.",
            "is_default": True,
        },
        "avatars": [
            {
                "name": "Director creativo Latam",
                "icp_description": "Freelance senior con 5+ años de cartera regional.",
                "is_default": True,
            },
        ],
        "offers": [_full_offer()],
        "has_team": False,
        "has_avatars": True,
        "has_offers": True,
        "has_testimonials": False,
        "has_authority": False,
        "personality_instruction": None,
        "style_anchors": None,
        "channel_type": "whatsapp",
        "has_legal_guardrails": False,
        "has_regulated_profession": False,
        "has_legal_documents": False,
    }


def _render(jinja_env: Environment) -> str:
    template = jinja_env.get_template("agent_identity.j2")
    return template.render(**_base_context())


def test_agent_identity_offer_block_byte_identical_to_golden(jinja_env: Environment) -> None:
    rendered = _render(jinja_env)

    if os.environ.get("REFRESH_GOLDEN") == "1":
        GOLDEN_PATH.write_text(rendered, encoding="utf-8")
        pytest.skip("Refreshed golden — re-run without REFRESH_GOLDEN=1 to validate.")

    assert GOLDEN_PATH.exists(), (
        f"Missing golden at {GOLDEN_PATH}. Generate first run via "
        "REFRESH_GOLDEN=1 .venv/bin/pytest tests/modules/sales_agent/test_agent_identity_offer_golden.py"
    )

    expected = GOLDEN_PATH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "agent_identity.j2 render drift detected vs golden snapshot. "
        "If intentional, refresh with REFRESH_GOLDEN=1 and audit the diff in the PR."
    )


def test_golden_contains_every_offer_field_label() -> None:
    """Sanity: golden covers the labels we expect — guards against accidental shrinkage."""
    expected = GOLDEN_PATH.read_text(encoding="utf-8") if GOLDEN_PATH.exists() else ""
    required_markers = (
        "**Tipo:**",
        "**Qué es:**",
        "**Señales clave:**",
        "**Promesa:**",
        "**Resultado Principal:**",
        "**Tiempo al Resultado:**",
        "**Precios:**",
        "**Impuestos:**",
        "**Cuotas sin interés disponibles:**",
        "**Métodos de pago aceptados:**",
        "**Garantía:**",
        "**Incluye:**",
        "**Dolores que resuelve:**",
        "**Deseos que satisface:**",
        "**Objeciones comunes y cómo manejarlas:**",
        "**Situación previa típica:**",
        "**Situación objetivo:**",
        "**Por qué actuar ahora:**",
        "**Resultados medibles:**",
        "**Barreras culturales Latam a anticipar:**",
        "**Disparadores emocionales:**",
        "**Motores de estatus:**",
        "**Escenarios de arrepentimiento",
        "**Urgencia honesta",
        "**Motivo de escasez real:**",
        "**Proceso de devolución:**",
        "**Bonus por decidir ahora:**",
        "**Cierre sugerido:**",
        "**Link de pago:**",
        "**Agendar llamada:**",
    )
    for marker in required_markers:
        assert marker in expected, (
            f"Golden snapshot is missing expected marker {marker!r}. "
            "Likely regression in synthetic offer fixture or template."
        )
