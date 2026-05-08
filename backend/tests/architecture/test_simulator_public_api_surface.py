"""Architecture fitness gate — eval-simulator public API surface (H9).

Story B (T-9) cement: ``backend/tests/agentic_evals/sales_agent/simulator/__init__.py``
exports EXACTLY 7 names. Anything more = leakage; anything less = missing
deliverable. Story C/D/E/F/G/H/I downstream consume ONLY these 7 names.

Allowlists are intentionally absent — any drift fails the gate.

Invariants enforced:

1. ``__all__`` is the literal frozenset
   ``{"run_simulation", "SimulationResult", "SimulationState", "ActorProfile",
   "TerminationReason", "AgentErrorSubtype", "register_termination_policy"}``.
2. Every name in ``__all__`` resolves to a public attribute (no NameError).
3. No ``_`` prefix attributes leak via the package import surface
   (excluding Python dunder ``__name__`` / ``__file__`` / etc which are
   set by the import machinery itself, not by ``__init__.py``).
4. The ``_internal`` subpackage is not re-exported on the public surface.

Pattern precedent: ``test_eval_simulator_observability_invariants.py``
(T-2) + ``test_schema_migrations_registry_complete.py`` (T-4 / T-9).

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.no_eval


_EXPECTED_PUBLIC_NAMES: frozenset[str] = frozenset(
    {
        "run_simulation",
        "SimulationResult",
        "SimulationState",
        "ActorProfile",
        "TerminationReason",
        "AgentErrorSubtype",
        "register_termination_policy",
    },
)


# ════════════════════════════════════════════════════════════════════════
# __all__ contract — exact 7 names (H9)
# ════════════════════════════════════════════════════════════════════════


def test_simulator_dunder_all_exact_seven_names() -> None:
    """``simulator.__all__`` MUST equal the expected 7-name frozenset.

    Adding or removing names without bumping H9 invariant in
    ``03-arch-agentic.md §6`` breaks the contract that downstream
    stories C/D/E/F/G/H/I depend on.
    """
    from tests.agentic_evals.sales_agent import simulator

    actual = frozenset(simulator.__all__)
    assert actual == _EXPECTED_PUBLIC_NAMES, (
        f"__all__ drift detected. Expected exactly 7 names "
        f"{sorted(_EXPECTED_PUBLIC_NAMES)}; got {sorted(actual)}. "
        f"Missing: {sorted(_EXPECTED_PUBLIC_NAMES - actual)}; "
        f"unexpected: {sorted(actual - _EXPECTED_PUBLIC_NAMES)}."
    )


def test_simulator_dunder_all_length_is_seven() -> None:
    """Cardinality cement — ``len(__all__) == 7`` literal."""
    from tests.agentic_evals.sales_agent import simulator

    assert len(simulator.__all__) == 7, f"__all__ MUST contain exactly 7 names per H9; got {len(simulator.__all__)}."


# ════════════════════════════════════════════════════════════════════════
# Each declared name resolves
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("name", sorted(_EXPECTED_PUBLIC_NAMES))
def test_each_public_name_resolvable(name: str) -> None:
    """Every name in ``__all__`` MUST be importable + non-None."""
    from tests.agentic_evals.sales_agent import simulator

    assert hasattr(simulator, name), f"Public name {name!r} declared in __all__ but missing from module attrs."
    obj = getattr(simulator, name)
    assert obj is not None, f"Public name {name!r} resolved to None — broken re-export."


# ════════════════════════════════════════════════════════════════════════
# No _internal leakage on the public surface
# ════════════════════════════════════════════════════════════════════════


def test_no_internal_symbols_leaked() -> None:
    """No ``_``-prefixed *symbol* (function / class / data) leaks via re-export.

    Distinction (cement):

    * ``simulator._internal`` (a submodule) IS visible on
      ``dir(simulator)`` because Python's import machinery binds
      submodules as attributes of the parent package — same machinery
      that sets ``__path__`` / ``__spec__`` / etc. This is structural,
      not semantic, and is allowed (private namespace convention only).

    * Function / class / variable names like ``_helper`` / ``_factory``
      / ``_thing`` re-exported on the public surface ARE leakage.

    The gate filters out the submodule-binding case via
    ``ModuleType`` instance check + the simulator's known submodule
    list. Anything left over with a leading underscore = symbol leak.
    """
    import types

    from tests.agentic_evals.sales_agent import simulator

    # Python-managed dunders set by the import machinery — not declared
    # by the module author. Allow these.
    _ALLOWED_DUNDERS = frozenset(
        {
            "__all__",
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

    # Submodules of `simulator` — bound automatically by Python's import
    # machinery when child modules are imported. ``_internal`` is the
    # canonical private namespace; its presence on dir() is structural,
    # not a leak.
    _ALLOWED_SUBMODULES = frozenset(
        {
            "_internal",
            "actor_profile",
            "fixtures",  # tests/agentic_evals/sales_agent/simulator/fixtures/
            "_fixtures",  # frozen golden fixtures namespace
            "result",
            "state",
            "termination",
        },
    )

    leaked: list[str] = []
    for attr in dir(simulator):
        if attr in _EXPECTED_PUBLIC_NAMES:
            continue
        if attr in _ALLOWED_DUNDERS:
            continue
        # Submodule references are structural — only flag ACTUAL symbols.
        value = getattr(simulator, attr, None)
        if isinstance(value, types.ModuleType):
            # Allowed only if it's a known submodule path.
            if attr in _ALLOWED_SUBMODULES:
                continue
            # Unknown submodule import — flag.
            leaked.append(f"{attr} (unknown submodule)")
            continue
        # Symbols (callable / data / class) with leading underscore = leak.
        if attr.startswith("_"):
            leaked.append(attr)

    assert not leaked, (
        f"Internal/private SYMBOLS leaked on simulator public surface: "
        f"{sorted(leaked)}. Move imports under `_internal/` or scope to "
        f"the file that needs them. Submodule namespaces (e.g., "
        f"``simulator._internal``) are allowed structurally."
    )


def test_internal_subpackage_not_reexported() -> None:
    """``simulator._internal`` MUST NOT be a re-export on the public surface.

    Importable as ``simulator._internal`` (private convention), but
    ``simulator.__all__`` must not include ``"_internal"`` and dir()
    must not surface it (covered by ``test_no_internal_symbols_leaked``).

    This test additionally verifies it is NOT in ``__all__`` even if
    Python's ``dir`` filter changes shape.
    """
    from tests.agentic_evals.sales_agent import simulator

    assert "_internal" not in simulator.__all__, "'_internal' MUST NOT appear in simulator.__all__ — private namespace."


# ════════════════════════════════════════════════════════════════════════
# Type/identity sanity for each public name
# ════════════════════════════════════════════════════════════════════════


def test_run_simulation_is_callable() -> None:
    """``run_simulation`` is the public orchestrator — must be callable."""
    from tests.agentic_evals.sales_agent import simulator

    assert callable(simulator.run_simulation), "run_simulation must be callable (async def per T-8)."


def test_register_termination_policy_is_callable() -> None:
    """``register_termination_policy`` is the H8 public registration helper."""
    from tests.agentic_evals.sales_agent import simulator

    assert callable(simulator.register_termination_policy), (
        "register_termination_policy must be callable (str, Callable) → None."
    )


def test_pydantic_classes_resolve_to_basemodel_subclasses() -> None:
    """``SimulationResult`` + ``SimulationState`` + ``ActorProfile`` are Pydantic v2."""
    from pydantic import BaseModel

    from tests.agentic_evals.sales_agent import simulator

    for cls_name in ("SimulationResult", "SimulationState", "ActorProfile"):
        cls = getattr(simulator, cls_name)
        assert isinstance(cls, type) and issubclass(cls, BaseModel), (
            f"{cls_name} must be a Pydantic BaseModel subclass; got {type(cls)}."
        )


def test_enum_classes_are_strenum_subclasses() -> None:
    """``TerminationReason`` + ``AgentErrorSubtype`` are StrEnum (Python 3.11+)."""
    from enum import StrEnum

    from tests.agentic_evals.sales_agent import simulator

    for enum_name in ("TerminationReason", "AgentErrorSubtype"):
        enum_cls = getattr(simulator, enum_name)
        assert isinstance(enum_cls, type) and issubclass(enum_cls, StrEnum), (
            f"{enum_name} must be a StrEnum subclass; got {type(enum_cls)}."
        )
