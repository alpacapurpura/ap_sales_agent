"""Tests for SafetyLayerService credit-card regex and SemanticRouter signal accumulation."""

import re
from unittest.mock import patch

from src.modules.sales_agent.application.services.semantic_router import SemanticRouter

# ─── Credit-card regex (same pattern used in SafetyLayerService Phase 2) ─────

CC_PATTERN = r"\b(?:\d{4}[-\s]?){3}\d{4}\b"


def test_credit_card_redacted():
    text = "Mi tarjeta es 4111-1111-1111-1111"
    result = re.sub(CC_PATTERN, "[REDACTED_PAYMENT_INFO]", text)
    assert "[REDACTED_PAYMENT_INFO]" in result
    assert "4111" not in result


def test_credit_card_spaces_redacted():
    text = "Numero: 5500 0000 0000 0004 por favor"
    result = re.sub(CC_PATTERN, "[REDACTED_PAYMENT_INFO]", text)
    assert "[REDACTED_PAYMENT_INFO]" in result
    assert "5500" not in result


def test_no_false_positive_short_number():
    text = "Mi codigo es 1234"
    result = re.sub(CC_PATTERN, "[REDACTED_PAYMENT_INFO]", text)
    assert "[REDACTED_PAYMENT_INFO]" not in result
    assert "1234" in result


# ─── SemanticRouter.detect_and_accumulate ────────────────────────────────────


def test_detect_and_accumulate_returns_tuple():
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("buying_signal", 0.85)
    ):
        result = SemanticRouter.detect_and_accumulate(
            "quiero comprar", existing_signals=[], tenant_id=None
        )
        assert isinstance(result, tuple)
        assert len(result) == 3
        intent, score, signals = result
        assert intent == "buying_signal"
        assert score == 0.85
        assert isinstance(signals, list)


def test_signal_accumulation_buying():
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("buying_signal", 0.85)
    ):
        intent, _score, signals = SemanticRouter.detect_and_accumulate(
            "quiero comprar", existing_signals=[], tenant_id=None
        )
        assert intent == "buying_signal"
        assert len(signals) == 1
        assert signals[0]["type"] == "buying_signal"
        assert signals[0]["confidence"] == 0.85
        assert signals[0]["turn"] == 0


def test_signal_accumulation_schedule():
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("schedule_signal", 0.72)
    ):
        intent, _score, signals = SemanticRouter.detect_and_accumulate(
            "quiero agendar una cita", existing_signals=[], tenant_id=None
        )
        assert intent == "schedule_signal"
        assert len(signals) == 1
        assert signals[0]["type"] == "schedule_signal"


def test_signal_accumulation_dedup():
    existing = [{"type": "buying_signal", "confidence": 0.80, "turn": 0}]
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("buying_signal", 0.90)
    ):
        _intent, _score, signals = SemanticRouter.detect_and_accumulate(
            "quiero pagar ya", existing_signals=existing, tenant_id=None
        )
        # Should NOT add a duplicate buying_signal
        assert len(signals) == 1
        assert signals[0]["confidence"] == 0.80  # original kept


def test_signal_accumulation_below_threshold():
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("buying_signal", 0.40)
    ):
        intent, _score, signals = SemanticRouter.detect_and_accumulate(
            "hmm no se", existing_signals=[], tenant_id=None
        )
        # Score below 0.50 threshold — no accumulation
        assert intent == "buying_signal"
        assert len(signals) == 0


def test_signal_accumulation_non_buying_intent():
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("objection_money", 0.92)
    ):
        intent, _score, signals = SemanticRouter.detect_and_accumulate(
            "es muy caro", existing_signals=[], tenant_id=None
        )
        # objection_money is not in buying_intents — no accumulation
        assert intent == "objection_money"
        assert len(signals) == 0


def test_signal_accumulation_does_not_mutate_original():
    original = [{"type": "schedule_signal", "confidence": 0.75, "turn": 0}]
    original_copy = list(original)
    with patch.object(
        SemanticRouter, "detect_intent", return_value=("buying_signal", 0.88)
    ):
        _, _, signals = SemanticRouter.detect_and_accumulate(
            "quiero comprar", existing_signals=original, tenant_id=None
        )
        # New list returned, original untouched
        assert len(signals) == 2
        assert len(original) == 1
        assert original == original_copy
