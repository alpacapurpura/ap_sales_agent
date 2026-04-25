"""Unit tests for ``build_question_hint`` (Fase 09.C).

Verifies the helper wraps ``next_question`` and produces a
ui_action-ready dict for guided advance enrichment.
"""

from __future__ import annotations

from src.modules.copilot.application.guided.question_hint import (
    build_question_hint,
)
from src.shared.domain.field_contract import (
    FieldContract,
    FieldStatus,
    FieldType,
    register_module_contracts,
)

_MODULE = "_synthetic_hint"


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
    human_question_es: str | None = None,
    label_es: str | None = None,
    expects: str | None = None,
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
        human_question_es=human_question_es,
        label_es=label_es,
        expects=expects,
    )


def test_returns_none_when_module_complete() -> None:
    register_module_contracts(_MODULE, (_c("a"),))
    assert build_question_hint(_MODULE, {"a": "v"}) is None


def test_returns_none_when_module_unknown() -> None:
    assert build_question_hint("module-does-not-exist", {}) is None


def test_uses_human_question_es_when_present() -> None:
    register_module_contracts(
        _MODULE,
        (_c("name", priority=10, human_question_es="¿Cómo se llama tu marca?"),),
    )
    hint = build_question_hint(_MODULE, {})
    assert hint is not None
    assert hint["question_es"] == "¿Cómo se llama tu marca?"
    assert hint["path"] == "name"


def test_falls_back_to_label_es_when_no_human_question() -> None:
    register_module_contracts(
        _MODULE,
        (_c("brand_name", priority=10, label_es="Razón social"),),
    )
    hint = build_question_hint(_MODULE, {})
    assert hint is not None
    assert hint["question_es"] == "Razón social"


def test_falls_back_to_humanized_path_when_no_meta() -> None:
    register_module_contracts(_MODULE, (_c("internal_sku", priority=10),))
    hint = build_question_hint(_MODULE, {})
    assert hint is not None
    assert hint["question_es"] == "Internal Sku"


def test_section_filter_passthrough() -> None:
    register_module_contracts(
        _MODULE,
        (
            _c("a", section="alpha", priority=10),
            _c("b", section="beta", priority=99),
        ),
    )
    hint = build_question_hint(_MODULE, {}, section="alpha")
    assert hint is not None
    assert hint["path"] == "a"


def test_payload_includes_expects_when_present() -> None:
    register_module_contracts(
        _MODULE,
        (_c("price", priority=10, expects="número en USD"),),
    )
    hint = build_question_hint(_MODULE, {})
    assert hint is not None
    assert hint["expects"] == "número en USD"


def test_payload_omits_expects_when_absent() -> None:
    register_module_contracts(_MODULE, (_c("name", priority=10),))
    hint = build_question_hint(_MODULE, {})
    assert hint is not None
    assert "expects" not in hint or hint["expects"] is None


def test_payload_includes_section() -> None:
    register_module_contracts(
        _MODULE,
        (_c("name", section="identity", priority=10),),
    )
    hint = build_question_hint(_MODULE, {})
    assert hint is not None
    assert hint["section"] == "identity"
