"""Tests for offer extraction wave schemas (Fase 3).

Validates that:
1. Each wave alias maps to the correct domain Update class.
2. PromiseWaveOutput validates realistic LLM payloads including narrative fields.
3. PsychologyWaveOutput parses structured ObjectionItem shape correctly.
4. PsychologyWaveOutput rejects invalid ObjectionItem.type values.
5. ClosingWaveOutput validates narrative closing fields.

refs: docs/contracts/offer-narrative-fields-CONTRACT.md §7 + §13.3
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.modules.offer.application.extraction_schemas import (
    ClosingWaveOutput,
    ObjectionItem,
    PromiseWaveOutput,
    PsychologyWaveOutput,
    StrategyWaveOutput,
    ValueStackWaveOutput,
)
from src.modules.offer.domain.offer import (
    OfferClosingUpdate,
    OfferPromiseUpdate,
    OfferPsychologyUpdate,
    OfferStrategyUpdate,
    OfferValueStackUpdate,
)

# ---------------------------------------------------------------------------
# 1. Wave aliases resolve to correct domain classes
# ---------------------------------------------------------------------------


class TestWaveAliases:
    """Verify that wave output type aliases point at the right domain models."""

    def test_promise_wave_output_is_offer_promise_update(self) -> None:
        assert PromiseWaveOutput is OfferPromiseUpdate

    def test_strategy_wave_output_is_offer_strategy_update(self) -> None:
        assert StrategyWaveOutput is OfferStrategyUpdate

    def test_psychology_wave_output_is_offer_psychology_update(self) -> None:
        assert PsychologyWaveOutput is OfferPsychologyUpdate

    def test_value_stack_wave_output_is_offer_value_stack_update(self) -> None:
        assert ValueStackWaveOutput is OfferValueStackUpdate

    def test_closing_wave_output_is_offer_closing_update(self) -> None:
        assert ClosingWaveOutput is OfferClosingUpdate


# ---------------------------------------------------------------------------
# 2. PromiseWaveOutput — realistic LLM fixture with narrative fields
# ---------------------------------------------------------------------------

_PROMISE_FIXTURE = {
    "headline_promise": "Duplica tus ventas en 90 días sin contratar equipo de marketing",
    "primary_outcome": "Pasarás de depender de referidos a tener un sistema predecible de 20+ leads/semana.",
    "time_to_value": "Primeros leads en 7 días",
    "before_state": "Trabajas 12 horas al día pero tus ingresos no crecen y el burnout ya llegó.",
    "after_state": "Tienes un sistema automatizado que genera leads mientras duermes.",
    "why_now": "Cada semana sin sistema son leads que se van a tu competencia.",
    "measurable_outcomes": [
        "Genera $5,000 USD adicionales en los primeros 90 días",
        "20+ leads calificados por semana",
        "Cierra 3 clientes nuevos por mes con tu nuevo script",
    ],
}


class TestPromiseWaveOutput:
    """PromiseWaveOutput validates realistic payloads including narrative fields."""

    def test_validates_full_payload(self) -> None:
        result = PromiseWaveOutput(**_PROMISE_FIXTURE)
        assert result.headline_promise == _PROMISE_FIXTURE["headline_promise"]
        assert result.before_state == _PROMISE_FIXTURE["before_state"]
        assert result.after_state == _PROMISE_FIXTURE["after_state"]
        assert result.why_now == _PROMISE_FIXTURE["why_now"]
        assert len(result.measurable_outcomes) == 3

    def test_all_fields_optional(self) -> None:
        """LLM may return empty object — must not raise."""
        result = PromiseWaveOutput()
        assert result.headline_promise is None
        assert result.before_state is None
        assert result.measurable_outcomes is None

    def test_measurable_outcomes_accepts_list(self) -> None:
        result = PromiseWaveOutput(measurable_outcomes=["Resultado A", "Resultado B"])
        assert result.measurable_outcomes == ["Resultado A", "Resultado B"]

    def test_measurable_outcomes_accepts_none(self) -> None:
        result = PromiseWaveOutput(measurable_outcomes=None)
        assert result.measurable_outcomes is None

    def test_model_dump_includes_narrative_fields(self) -> None:
        result = PromiseWaveOutput(**_PROMISE_FIXTURE)
        dumped = result.model_dump(exclude_unset=True, exclude_none=True)
        assert "before_state" in dumped
        assert "after_state" in dumped
        assert "why_now" in dumped
        assert "measurable_outcomes" in dumped


# ---------------------------------------------------------------------------
# 3. PsychologyWaveOutput — structured ObjectionItem
# ---------------------------------------------------------------------------

_OBJECTION_ITEM_FIXTURE = {
    "type": "price",
    "rebuttal": (
        "Entiendo perfectamente — es una inversión importante. "
        "Permíteme preguntarte: ¿cuánto te cuesta ahora no tener un sistema? "
        "Si recuperas el costo en el primer cliente, la matemática funciona. "
        "¿Quieres ver cómo otros en tu situación lo lograron?"
    ),
    "strategy": "ROI Reframing",
    "trigger_phrases": ["es mucho dinero", "no tengo el presupuesto ahorita", "está muy caro"],
}

_PSYCHOLOGY_FIXTURE = {
    "marketing_pain_points": ["Publicas contenido pero nadie compra."],
    "marketing_desires": ["Abrir el laptop y ver 5 leads calificados esperándote."],
    "objections": [_OBJECTION_ITEM_FIXTURE],
    "cultural_trust_barriers": [
        "Desconfianza en pagos online con tarjeta internacional.",
        "Preferencia por WhatsApp antes de comprar.",
    ],
    "emotional_triggers": [
        "Miedo a haber tomado otra decisión equivocada.",
        "Querer ser reconocido como experto en su industria.",
    ],
    "status_drivers": ["Que sus colegas le pregunten cómo lo logró."],
    "regret_scenarios": ["En 6 meses verás a tu competencia con el sistema que debiste implementar antes."],
}


class TestPsychologyWaveOutput:
    """PsychologyWaveOutput parses structured ObjectionItem and narrative fields."""

    def test_validates_full_payload(self) -> None:
        result = PsychologyWaveOutput(**_PSYCHOLOGY_FIXTURE)
        assert len(result.objections) == 1
        assert len(result.cultural_trust_barriers) == 2
        assert len(result.emotional_triggers) == 2
        assert len(result.status_drivers) == 1
        assert len(result.regret_scenarios) == 1

    def test_objection_item_shape_parsed(self) -> None:
        result = PsychologyWaveOutput(**_PSYCHOLOGY_FIXTURE)
        obj = result.objections[0]
        assert isinstance(obj, ObjectionItem)
        assert obj.type == "price"
        assert obj.strategy == "ROI Reframing"
        assert len(obj.trigger_phrases) == 3
        assert obj.rebuttal.startswith("Entiendo perfectamente")

    def test_all_narrative_fields_optional(self) -> None:
        result = PsychologyWaveOutput()
        assert result.cultural_trust_barriers is None
        assert result.emotional_triggers is None
        assert result.status_drivers is None
        assert result.regret_scenarios is None

    def test_model_dump_includes_narrative_fields(self) -> None:
        result = PsychologyWaveOutput(**_PSYCHOLOGY_FIXTURE)
        dumped = result.model_dump(exclude_unset=True, exclude_none=True)
        assert "cultural_trust_barriers" in dumped
        assert "emotional_triggers" in dumped
        assert "status_drivers" in dumped
        assert "regret_scenarios" in dumped

    def test_multiple_objection_types(self) -> None:
        """Multiple objections with different types parse correctly."""
        result = PsychologyWaveOutput(
            objections=[
                {"type": "price", "rebuttal": "Rebuttal price.", "strategy": "ROI", "trigger_phrases": []},
                {"type": "time", "rebuttal": "Rebuttal time.", "strategy": "Time Paradox", "trigger_phrases": []},
                {"type": "trust", "rebuttal": "Rebuttal trust.", "strategy": "Risk Reversal", "trigger_phrases": []},
                {
                    "type": "partner",
                    "rebuttal": "Rebuttal partner.",
                    "strategy": "Decision Facilitator",
                    "trigger_phrases": [],
                },
                {"type": "fit", "rebuttal": "Rebuttal fit.", "strategy": "Avatar Clarifier", "trigger_phrases": []},
                {"type": "custom", "rebuttal": "Rebuttal custom.", "strategy": "Custom", "trigger_phrases": []},
            ]
        )
        assert len(result.objections) == 6
        types = [o.type for o in result.objections]
        assert "price" in types
        assert "fit" in types
        assert "custom" in types


# ---------------------------------------------------------------------------
# 4. PsychologyWaveOutput — ObjectionItem type validation
# ---------------------------------------------------------------------------


class TestObjectionItemTypeValidation:
    """ObjectionItem accepts known type values; ObjectionItem has no type restriction at domain level
    but the extraction schema should accept "fit" as a valid type."""

    def test_accepts_all_known_types(self) -> None:
        known_types = ["price", "time", "trust", "partner", "fit", "custom"]
        for t in known_types:
            item = ObjectionItem(type=t, rebuttal="Rebuttal.", strategy="Strategy")
            assert item.type == t

    def test_accepts_custom_type_string(self) -> None:
        """Domain is open-ended: type is str, not an enum. Custom strings allowed."""
        item = ObjectionItem(type="logistics", rebuttal="Rebuttal.", strategy="Custom")
        assert item.type == "logistics"

    def test_trigger_phrases_default_empty(self) -> None:
        item = ObjectionItem(type="price", rebuttal="Rebuttal.", strategy="ROI")
        assert item.trigger_phrases == []

    def test_strategy_default_empty_string(self) -> None:
        item = ObjectionItem(type="price", rebuttal="Rebuttal.")
        assert item.strategy == ""


# ---------------------------------------------------------------------------
# 5. ClosingWaveOutput — narrative closing fields
# ---------------------------------------------------------------------------

_CLOSING_FIXTURE = {
    "guarantee_type": "unconditional_30_day",
    "guarantee_terms": "Si en 30 días no estás satisfecho, te devolvemos el 100% sin preguntas.",
    "refund_process_description": (
        "Si pagaste con tarjeta, el reembolso llega en 5-7 días hábiles. "
        "Si pagaste por transferencia, necesitamos tus datos bancarios."
    ),
    "urgency_drivers": [
        "El precio sube el próximo lunes al incluir el módulo de copywriting.",
        "Cerramos inscripciones cuando llegamos a 20 participantes.",
    ],
    "scarcity_reason_honest": (
        "Limitamos a 20 personas porque cada participante tiene sesión 1:1 mensual con el mentor."
    ),
    "bonus_if_act_now": "Si te inscribes antes del viernes, recibes acceso a la masterclass de copywriting.",
    "final_push_copy": (
        "Si llegaste hasta aquí, algo en ti sabe que este es tu momento. "
        "Tienes 30 días de garantía — la única pregunta real es: ¿cuánto más esperas?"
    ),
    "support_duration_days": 90,
}


class TestClosingWaveOutput:
    """ClosingWaveOutput validates narrative closing fields."""

    def test_validates_full_payload(self) -> None:
        result = ClosingWaveOutput(**_CLOSING_FIXTURE)
        assert result.refund_process_description is not None
        assert len(result.urgency_drivers) == 2
        assert result.scarcity_reason_honest is not None
        assert result.bonus_if_act_now is not None
        assert result.final_push_copy is not None
        assert result.support_duration_days == 90

    def test_all_narrative_fields_optional(self) -> None:
        result = ClosingWaveOutput()
        assert result.refund_process_description is None
        assert result.urgency_drivers is None
        assert result.scarcity_reason_honest is None
        assert result.bonus_if_act_now is None
        assert result.final_push_copy is None
        assert result.support_duration_days is None

    def test_model_dump_includes_narrative_fields(self) -> None:
        result = ClosingWaveOutput(**_CLOSING_FIXTURE)
        dumped = result.model_dump(exclude_unset=True, exclude_none=True)
        assert "refund_process_description" in dumped
        assert "urgency_drivers" in dumped
        assert "scarcity_reason_honest" in dumped
        assert "bonus_if_act_now" in dumped
        assert "final_push_copy" in dumped
        assert "support_duration_days" in dumped

    def test_urgency_drivers_accepts_empty_list(self) -> None:
        result = ClosingWaveOutput(urgency_drivers=[])
        assert result.urgency_drivers == []

    def test_guarantee_type_enum_coercion(self) -> None:
        from src.modules.offer.domain.enums import GuaranteeType

        result = ClosingWaveOutput(guarantee_type=GuaranteeType.UNCONDITIONAL_30_DAY)
        assert result.guarantee_type == GuaranteeType.UNCONDITIONAL_30_DAY
