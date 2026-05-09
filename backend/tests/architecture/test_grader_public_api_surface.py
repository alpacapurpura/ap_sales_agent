"""Architecture fitness gate — grader public API surface (D-AG-16 cement).

Story E (sales-agent-voice-fidelity-grader-runtime) cement:
``backend/tests/agentic_evals/sales_agent/grader/__init__.py`` exports
EXACTLY 0 names. The grader package is a private namespace; downstream
consumers reach the public entrypoint ``grade_transcript_maj_eval`` via
``simulator/__init__.py`` (H9 expand 7→8 — single addition path).

Surface controlled via simulator/__init__.py expand only.

Invariants enforced:

1. ``grader.__all__`` is the literal empty list ``[]`` (zero re-exports).
2. ``grader._internal.__all__`` is also empty (private internal namespace).
3. ``grade_transcript_maj_eval`` resolves via the H9 path
   ``from tests.agentic_evals.sales_agent.simulator import grade_transcript_maj_eval``.
4. ``grade_transcript_maj_eval`` does NOT resolve directly via
   ``from tests.agentic_evals.sales_agent.grader import ...``.
5. The ``grader/`` package does not surface any public symbol on dir() that
   would constitute a re-export (no ``_``-prefixed symbols leak; submodule
   bindings from import machinery are allowed).

Allowlists are intentionally absent — any drift fails the gate.

Pattern precedent: ``test_simulator_public_api_surface.py`` (Story B T-9 +
Story E T-8 H9 expand).

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# grader/__init__.py __all__ contract — empty (zero re-exports)
# ════════════════════════════════════════════════════════════════════════


def test_grader_dunder_all_is_empty_list() -> None:
    """``grader.__all__`` MUST equal ``[]`` — cero re-exports (D-AG-16 cement).

    Public surface for grader runtime is controlled exclusively via
    ``simulator/__init__.py`` H9 expand 7→8. Adding any name to
    ``grader.__all__`` breaks the invariant that the simulator package is
    the single canonical entrypoint.
    """
    from tests.agentic_evals.sales_agent import grader

    assert grader.__all__ == [], (
        f"grader.__all__ MUST be empty (zero re-exports per D-AG-16). Got "
        f"{sorted(grader.__all__)}. Public surface controlled via "
        f"simulator/__init__.py expand only."
    )


def test_grader_dunder_all_length_is_zero() -> None:
    """Cardinality cement — ``len(grader.__all__) == 0`` literal."""
    from tests.agentic_evals.sales_agent import grader

    assert len(grader.__all__) == 0, (
        f"grader.__all__ MUST contain exactly 0 names per D-AG-16; got {len(grader.__all__)}."
    )


def test_grader_internal_dunder_all_is_empty_list() -> None:
    """``grader._internal.__all__`` MUST equal ``[]`` — internal namespace is private."""
    from tests.agentic_evals.sales_agent.grader import _internal

    assert _internal.__all__ == [], (
        f"grader._internal.__all__ MUST be empty (private namespace). Got {sorted(_internal.__all__)}."
    )


# ════════════════════════════════════════════════════════════════════════
# grade_transcript_maj_eval resolves via H9 expand path (simulator)
# ════════════════════════════════════════════════════════════════════════


def test_grade_transcript_maj_eval_accessible_via_simulator() -> None:
    """The H9 expand path is the canonical access route for grader runtime.

    ``from tests.agentic_evals.sales_agent.simulator import grade_transcript_maj_eval``
    MUST succeed and return a callable (the async orchestrator from
    ``grader/_internal/maj_eval.py``).
    """
    from tests.agentic_evals.sales_agent.simulator import grade_transcript_maj_eval

    assert grade_transcript_maj_eval is not None, (
        "grade_transcript_maj_eval re-export missing from simulator/__init__.py — "
        "H9 expand 7→8 broken. Verify simulator/__init__.py imports the function "
        "from grader/_internal/maj_eval.py and includes it in __all__."
    )
    assert callable(grade_transcript_maj_eval), (
        f"grade_transcript_maj_eval must be callable (async def per T-5); got {type(grade_transcript_maj_eval)}."
    )


def test_grade_transcript_maj_eval_in_simulator_dunder_all() -> None:
    """``grade_transcript_maj_eval`` MUST appear in ``simulator.__all__`` post H9 expand."""
    from tests.agentic_evals.sales_agent import simulator

    assert "grade_transcript_maj_eval" in simulator.__all__, (
        f"grade_transcript_maj_eval missing from simulator.__all__ — H9 expand 7→8 "
        f"broken. Got {sorted(simulator.__all__)}."
    )


def test_grade_transcript_maj_eval_not_re_exported_from_grader_package() -> None:
    """Grader package MUST NOT re-export ``grade_transcript_maj_eval`` directly.

    The function lives at ``grader._internal.maj_eval.grade_transcript_maj_eval`` —
    accessible via that explicit path for tests within the grader subtree, but
    NOT surfaced as ``grader.grade_transcript_maj_eval`` (would constitute a
    re-export, violating D-AG-16 cement).
    """
    from tests.agentic_evals.sales_agent import grader

    # The name must not be in __all__.
    assert "grade_transcript_maj_eval" not in grader.__all__, (
        "grade_transcript_maj_eval MUST NOT appear in grader.__all__ per D-AG-16. "
        "Surface controlled via simulator/__init__.py H9 expand only."
    )

    # The name must not be a top-level attribute of the grader package itself
    # (it is fine to access via ``grader._internal.maj_eval.grade_transcript_maj_eval``
    # but ``grader.grade_transcript_maj_eval`` MUST NOT resolve as a re-export).
    assert not hasattr(grader, "grade_transcript_maj_eval"), (
        "grade_transcript_maj_eval re-exported via grader/__init__.py — D-AG-16 "
        "violated. Remove the import from grader/__init__.py; access only via "
        "simulator/__init__.py H9 expand path."
    )


# ════════════════════════════════════════════════════════════════════════
# No private symbol leakage on grader public surface
# ════════════════════════════════════════════════════════════════════════


def test_no_internal_symbols_leaked_on_grader() -> None:
    """No ``_``-prefixed *symbol* (function / class / data) leaks via re-export.

    Distinction (cement):

    * ``grader._internal`` (a submodule) IS visible on ``dir(grader)``
      because Python's import machinery binds submodules as attributes
      of the parent package — same machinery that sets ``__path__`` /
      ``__spec__`` / etc. This is structural, not semantic, and is allowed.
    * Function / class / variable names like ``_helper`` / ``_factory``
      re-exported on the public surface ARE leakage.
    """
    import types

    from tests.agentic_evals.sales_agent import grader

    # Python-managed dunders set by the import machinery — not declared
    # by the module author. Allow these. ``__annotations__`` is set when
    # the module declares a type-annotated assignment (e.g.,
    # ``__all__: list[str] = []``), which the grader package does
    # intentionally — that annotation is structural, not semantic.
    _ALLOWED_DUNDERS = frozenset(
        {
            "__all__",
            "__annotations__",
            "__builtins__",
            "__cached__",
            "__doc__",
            "__file__",
            "__loader__",
            "__name__",
            "__package__",
            "__path__",
            "__spec__",
        },
    )

    # Submodules of `grader` — bound automatically by Python's import
    # machinery when child modules are imported. ``_internal`` is the
    # canonical private namespace; its presence on dir() is structural.
    _ALLOWED_SUBMODULES = frozenset(
        {
            "_internal",
            "result",  # backend/tests/agentic_evals/sales_agent/grader/result.py — Pydantic types
        },
    )

    leaked: list[str] = []
    for attr in dir(grader):
        if attr in _ALLOWED_DUNDERS:
            continue
        # Test modules + conftest bound by pytest collection on the parent
        # package — structural, not semantic re-export.
        if attr.startswith("test_") or attr == "conftest":
            continue
        # Submodule references are structural — only flag ACTUAL symbols.
        value = getattr(grader, attr, None)
        if isinstance(value, types.ModuleType):
            if attr in _ALLOWED_SUBMODULES:
                continue
            # Unknown submodule import on the public surface — flag.
            leaked.append(f"{attr} (unknown submodule)")
            continue
        # Symbols (callable / data / class) with leading underscore = leak.
        if attr.startswith("_"):
            leaked.append(attr)

    assert not leaked, (
        f"Internal/private SYMBOLS leaked on grader public surface: "
        f"{sorted(leaked)}. Move imports under `_internal/` or scope them to "
        f"the file that needs them. Submodule namespaces (e.g., "
        f"``grader._internal``) are allowed structurally."
    )


def test_internal_subpackage_not_reexported_on_grader() -> None:
    """``grader._internal`` MUST NOT be a re-export on the public surface.

    Importable as ``grader._internal`` (private convention), but
    ``grader.__all__`` must not include ``"_internal"``.
    """
    from tests.agentic_evals.sales_agent import grader

    assert "_internal" not in grader.__all__, "'_internal' MUST NOT appear in grader.__all__ — private namespace."
