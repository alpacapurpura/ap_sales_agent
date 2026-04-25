"""Golden snapshot for landing content builders.

Locks each archetype builder's output for a synthetic offer dict that
covers every field the builders read. Future refactors must keep this
file green to prove that landing copy doesn't drift.

Refresh: ``REFRESH_GOLDEN=1 .venv/bin/pytest tests/modules/landing/application/test_landing_builders_golden.py``.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from src.modules.landing.application.landing_content_builders import (
    _build_brochure_content,
    _build_event_content,
    _build_flash_offer_content,
    _build_squeeze_content,
    _build_transformer_content,
    _build_velvet_rope_content,
)

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "landing_builders_golden.json"


def _full_offer_data() -> dict[str, Any]:
    """Synthetic offer covering every field the landing builders read."""
    return {
        "name": "Programa Alquimia LATAM",
        "headline_promise": "Pasa de freelance reactivo a estudio rentable en 90 días",
        "after_state": "Atendés solo clientes premium que valoran tu criterio.",
        "before_state": "Trabajás 60 horas semanales atendiendo clientes que regatean precio.",
        "primary_outcome": "Pipeline de clientes premium recurrente",
        "why_now": "Cada mes que postergás es un cliente premium que tu competencia capta.",
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
        "measurable_outcomes": [
            "Ticket promedio +250%",
            "Margen operativo +40 pp",
            "Tiempo facturable -50%",
        ],
        "regret_scenarios": [
            "Dentro de 12 meses seguir cobrando lo mismo.",
            "Ver competidores posicionarse como referentes.",
        ],
        "urgency_drivers": [
            "Cohorte cierra el viernes",
            "Bonus mentoría para los primeros 5",
        ],
        "scarcity_reason_honest": "Solo 12 plazas para mantener calidad de mentoría 1:1.",
        "anti_avatar_keywords": ["estudiante", "principiante"],
        "deliverables": [
            {"name": "12 sesiones grupales en vivo", "format": "live", "fulfillment_note": "Lunes 18hs"},
            {"name": "Plantillas y SOPs operativos", "format": "pdf"},
            {"name": "Mentoría 1:1 mensual", "format": "live"},
            {"name": "Acceso a comunidad", "format": "discord"},
            {"name": "Auditoría privada", "format": "live"},
            {"name": "Biblioteca de templates", "format": "notion"},
            {"name": "Sesión bonus de pricing", "format": "live"},
        ],
        "pricing": {
            "pay_in_full": 1497.0,
            "original_price": 1997.0,
            "discounted_price": 997.0,
        },
        "final_push_copy": "Listo. ¿Vas con pago único o cuotas?",
    }


def _empty_offer_data() -> dict[str, Any]:
    """Offer with the minimal field set; verifies fallback paths."""
    return {
        "name": "Oferta mínima",
    }


def _build_all(data: dict[str, Any]) -> dict[str, Any]:
    """Run every builder and serialise output to a comparable dict."""
    results: dict[str, Any] = {}
    for name, builder in (
        ("squeeze", _build_squeeze_content),
        ("transformer", _build_transformer_content),
        ("brochure", _build_brochure_content),
        ("velvet_rope", _build_velvet_rope_content),
        ("event", _build_event_content),
        ("flash_offer", _build_flash_offer_content),
    ):
        content = builder(data)
        results[name] = content.model_dump(mode="json") if content is not None else None
    return results


def _produce_golden() -> dict[str, Any]:
    return {
        "full": _build_all(_full_offer_data()),
        "empty": _build_all(_empty_offer_data()),
    }


def test_landing_builders_byte_identical_to_golden() -> None:
    actual = _produce_golden()

    if os.environ.get("REFRESH_GOLDEN") == "1":
        GOLDEN_PATH.write_text(
            json.dumps(actual, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pytest.skip("Refreshed golden — re-run without REFRESH_GOLDEN=1 to validate.")

    assert GOLDEN_PATH.exists(), (
        f"Missing golden at {GOLDEN_PATH}. Generate via "
        "REFRESH_GOLDEN=1 .venv/bin/pytest tests/modules/landing/application/test_landing_builders_golden.py"
    )

    expected = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert actual == expected, (
        "Landing builder output drift detected vs golden snapshot. "
        "If intentional, refresh with REFRESH_GOLDEN=1 and audit the diff."
    )
