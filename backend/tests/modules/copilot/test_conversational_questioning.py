"""Unit tests for ``next_question`` channel-agnostic algorithm (Fase 09.B).

The algorithm must be a pure function over a synthetic FieldContract
registry — no DB, no LLM, no I/O. We build a tiny fake module
``_synthetic_q`` and exercise every branch of the selection rule.
``teardown_module`` clears the synthetic module so the global registry
stays clean for the rest of the suite (no cross-domain duplicates).
"""

from __future__ import annotations

import pytest

from luana_core_copilot.application.orchestrator.conversational_questioning import (
    _gate_satisfied,
    _get_path,
    _is_missing,
    next_question,
)
from luana_core_platform.domain.field_contract import (
    FieldContract,
    FieldStatus,
    FieldType,
    register_module_contracts,
)

_MODULE = "_synthetic_q"


def teardown_module(module: object) -> None:
    """Drop synthetic module from the global registry to keep cross-test isolation."""
    register_module_contracts(_MODULE, ())


def _c(
    path: str,
    *,
    section: str = "main",
    priority: int = 0,
    is_required_semantic: bool = True,
    can_propose: bool = True,
    status: FieldStatus = FieldStatus.ACTIVE,
    gate: str | None = None,
    human_question_es: str | None = None,
) -> FieldContract:
    return FieldContract(
        path=path,
        owner_module=_MODULE,
        type=FieldType.TEXT,
        is_required_structural=False,
        section=section,
        priority=priority,
        is_required_semantic=is_required_semantic,
        can_propose=can_propose,
        status=status,
        gate=gate,
        human_question_es=human_question_es,
    )


def _register(*contracts: FieldContract) -> None:
    register_module_contracts(_MODULE, tuple(contracts))


# --------------------------------------------------------------------------- #
# Helpers — _is_missing                                                       #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", [], {}, ()],
)
def test_is_missing_true(value: object) -> None:
    assert _is_missing(value) is True


@pytest.mark.parametrize(
    "value",
    [0, 0.0, False, "x", [0], {"k": "v"}, ("x",)],
)
def test_is_missing_false(value: object) -> None:
    assert _is_missing(value) is False


# --------------------------------------------------------------------------- #
# Helpers — _get_path                                                         #
# --------------------------------------------------------------------------- #


def test_get_path_top_level() -> None:
    assert _get_path({"a": 1}, "a") == 1


def test_get_path_nested() -> None:
    assert _get_path({"a": {"b": "x"}}, "a.b") == "x"


def test_get_path_missing_returns_none() -> None:
    assert _get_path({"a": 1}, "b") is None
    assert _get_path({"a": {"b": 1}}, "a.c") is None


def test_get_path_through_non_dict_returns_none() -> None:
    assert _get_path({"a": "scalar"}, "a.b") is None


# --------------------------------------------------------------------------- #
# Helpers — _gate_satisfied                                                   #
# --------------------------------------------------------------------------- #


def test_gate_none_always_satisfied() -> None:
    assert _gate_satisfied(None, {}) is True
    assert _gate_satisfied(None, {"x": 1}) is True


def test_gate_satisfied_when_path_populated() -> None:
    assert _gate_satisfied("x", {"x": "v"}) is True
    assert _gate_satisfied("a.b", {"a": {"b": "v"}}) is True


def test_gate_unsatisfied_when_path_missing() -> None:
    assert _gate_satisfied("x", {}) is False
    assert _gate_satisfied("x", {"x": ""}) is False
    assert _gate_satisfied("x", {"x": []}) is False


# --------------------------------------------------------------------------- #
# next_question — selection rules                                             #
# --------------------------------------------------------------------------- #


def test_empty_state_returns_first_required_by_priority() -> None:
    _register(
        _c("low", priority=1),
        _c("high", priority=10),
        _c("mid", priority=5),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.path == "high"


def test_field_with_value_not_offered() -> None:
    _register(
        _c("filled", priority=10),
        _c("empty", priority=5),
    )
    result = next_question(_MODULE, {"filled": "yes"})
    assert result is not None
    assert result.path == "empty"


def test_gate_unsatisfied_field_skipped() -> None:
    _register(
        _c("a", priority=10, gate="archetype"),
        _c("b", priority=5),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.path == "b", "gate=archetype unsatisfied → 'a' must be skipped"


def test_gate_satisfied_field_offered() -> None:
    _register(
        _c("a", priority=10, gate="archetype"),
        _c("b", priority=5),
    )
    result = next_question(_MODULE, {"archetype": "PRODUCTIZED_SERVICE"})
    assert result is not None
    assert result.path == "a"


def test_status_deprecated_excluded() -> None:
    _register(
        _c("legacy", priority=10, status=FieldStatus.DEPRECATED),
        _c("active", priority=5),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.path == "active"


def test_status_removed_excluded() -> None:
    _register(
        _c("removed", priority=10, status=FieldStatus.REMOVED),
        _c("active", priority=5),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.path == "active"


def test_can_propose_false_excluded() -> None:
    _register(
        _c("readonly", priority=10, can_propose=False),
        _c("editable", priority=5),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.path == "editable"


def test_required_first_ordering() -> None:
    """Required-missing wins over optional-missing regardless of priority."""
    _register(
        _c("optional_high", priority=99, is_required_semantic=False),
        _c("required_low", priority=1, is_required_semantic=True),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.path == "required_low"


def test_optional_offered_when_no_required_missing() -> None:
    _register(
        _c("required_filled", priority=10, is_required_semantic=True),
        _c("optional_empty", priority=5, is_required_semantic=False),
    )
    result = next_question(_MODULE, {"required_filled": "v"})
    assert result is not None
    assert result.path == "optional_empty"


def test_tie_break_by_section_then_priority_then_path() -> None:
    _register(
        _c("zzz", section="alpha", priority=10),
        _c("aaa", section="beta", priority=10),
        _c("bbb", section="alpha", priority=10),
    )
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.section == "alpha"
    assert result.path == "bbb", "alpha section wins; within priority tie path lex order"


def test_section_filter_restricts_candidates() -> None:
    _register(
        _c("a_main", section="main", priority=10),
        _c("a_extra", section="extra", priority=99),
    )
    result = next_question(_MODULE, {}, section="extra")
    assert result is not None
    assert result.path == "a_extra"


def test_empty_list_counts_missing() -> None:
    _register(_c("paths", priority=10))
    result = next_question(_MODULE, {"paths": []})
    assert result is not None
    assert result.path == "paths"


def test_empty_dict_counts_missing() -> None:
    _register(_c("attrs", priority=10))
    result = next_question(_MODULE, {"attrs": {}})
    assert result is not None
    assert result.path == "attrs"


def test_blank_string_counts_missing() -> None:
    _register(_c("name", priority=10))
    result = next_question(_MODULE, {"name": "   "})
    assert result is not None
    assert result.path == "name"


def test_false_boolean_not_missing() -> None:
    _register(
        _c("flag", priority=10),
        _c("other", priority=5),
    )
    result = next_question(_MODULE, {"flag": False})
    assert result is not None
    assert result.path == "other", "False is not missing — skip 'flag'"


def test_zero_number_not_missing() -> None:
    _register(
        _c("count", priority=10),
        _c("other", priority=5),
    )
    result = next_question(_MODULE, {"count": 0})
    assert result is not None
    assert result.path == "other"


def test_module_complete_returns_none() -> None:
    _register(
        _c("a", priority=10),
        _c("b", priority=5),
    )
    result = next_question(_MODULE, {"a": "v", "b": "v"})
    assert result is None


def test_module_with_no_candidates_returns_none() -> None:
    _register(
        _c("only_optional_filled", priority=10, is_required_semantic=False),
    )
    result = next_question(_MODULE, {"only_optional_filled": "v"})
    assert result is None


def test_unregistered_module_returns_none() -> None:
    result = next_question("module_that_does_not_exist", {})
    assert result is None


def test_human_question_es_preserved_on_returned_contract() -> None:
    _register(_c("greeting", priority=10, human_question_es="¿Cómo te llamas?"))
    result = next_question(_MODULE, {})
    assert result is not None
    assert result.human_question_es == "¿Cómo te llamas?"
