"""Architecture fitness gate — eval-simulator anti-mirror cement (H9 + §0).

Story B (T-9) cement: NO file under
``backend/tests/agentic_evals/sales_agent/simulator/`` (or its
``_internal/`` subpackage) may duplicate the *basename* of a file that
already exists under ``backend/src/shared/agent_observability/``.

The ratchet is intentional. ``observability.py`` /
``callback_handler.py`` / ``turn_envelope.py`` / ``cost_recorder.py`` /
``calculator.py`` / ``fx_resolver.py`` and friends MUST be imported via
the canonical ``shared/`` paths — duplication here was the trigger for
``.claude/rules/anti-duplication.md`` (PR-1 PI-1.1 hotfix 2026-05-01).

Subclass exemption
==================

A simulator file MAY share a basename with a shared file IF AND ONLY IF:

* It is ``__init__.py`` (allowed everywhere — namespace marker).
* OR it declares at least one class that subclasses a class defined
  in the matching shared file. ``EvalSimulatorObservabilityContext``
  subclasses ``BaseObservabilityContext`` from
  ``shared/agent_observability/recording/turn_envelope.py`` — but the
  simulator copy is named ``observability.py``, not ``turn_envelope.py``,
  so this gate fires zero false positives in Story B.

Allowlists are intentionally absent — any drift fails the gate.

Pattern precedent: ``test_eval_simulator_observability_invariants.py``
(T-2) uses path-walk + AST. This gate uses path-walk + basename-set
intersection (faster + more deterministic).

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval


# Repo root anchor — `backend/` two levels up from this test file.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_SHARED_OBS_ROOT: Path = _BACKEND_ROOT / "src" / "shared" / "agent_observability"
_SIMULATOR_ROOT: Path = _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "simulator"

# Always-allowed basenames (namespace markers, no logic).
_ALLOWED_BASENAMES: frozenset[str] = frozenset({"__init__.py"})


def _walk_python_basenames(root: Path) -> dict[str, list[Path]]:
    """Return a basename → list[absolute path] map for ``*.py`` under ``root``.

    A basename appearing more than once across the shared tree (e.g.,
    ``__init__.py``) maps to multiple paths.
    """
    out: dict[str, list[Path]] = {}
    for p in root.rglob("*.py"):
        # Skip __pycache__ if rglob ever surfaced it.
        if "__pycache__" in p.parts:
            continue
        out.setdefault(p.name, []).append(p)
    return out


def _shared_class_names(shared_path: Path) -> set[str]:
    """Parse a shared file and collect top-level class names.

    Used to verify subclass-exemption: a simulator file with a colliding
    basename is allowed IF it imports + subclasses one of these classes.
    Story B doesn't actually trigger this exemption (no basename collision
    in the current tree), but the helper is wired for future churn.
    """
    try:
        tree = ast.parse(shared_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _simulator_file_subclasses_any(simulator_path: Path, expected: set[str]) -> bool:
    """Return True iff ``simulator_path`` defines a class extending one of ``expected``.

    Defense: when a future build deliberately co-locates a same-basename
    subclass file (highly unusual), the gate doesn't fire. Story B does
    not exercise this path — it's documented as a forward exit.
    """
    try:
        tree = ast.parse(simulator_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            base_name: str | None = None
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name and base_name in expected:
                return True
    return False


# ════════════════════════════════════════════════════════════════════════
# Smoke + path existence
# ════════════════════════════════════════════════════════════════════════


def test_shared_observability_root_exists() -> None:
    """Sanity — guard against repo-layout drift breaking the gate silently."""
    assert _SHARED_OBS_ROOT.is_dir(), (
        f"Shared agent_observability root not found at {_SHARED_OBS_ROOT}; "
        f"repo layout drift detected — update this gate."
    )


def test_simulator_root_exists() -> None:
    """Sanity — simulator package exists post T-1..T-9."""
    assert _SIMULATOR_ROOT.is_dir(), (
        f"Simulator package root not found at {_SIMULATOR_ROOT}; T-4..T-8 deliverables missing."
    )


# ════════════════════════════════════════════════════════════════════════
# Basename collision detection — main invariant (no allowlist)
# ════════════════════════════════════════════════════════════════════════


def test_no_basename_collision_with_shared_observability() -> None:
    """Cero simulator basename ∈ shared/agent_observability basenames.

    Subclass exemption documented above. Story B asserts no collisions
    exist — future builds that legitimately co-locate a same-basename
    subclass file MUST justify in the test docstring + add an
    explicit allowlist (which we deliberately avoid right now).
    """
    shared_basenames = set(_walk_python_basenames(_SHARED_OBS_ROOT))
    simulator_basenames = _walk_python_basenames(_SIMULATOR_ROOT)

    collisions: list[tuple[str, list[Path]]] = []
    for basename, sim_paths in simulator_basenames.items():
        if basename in _ALLOWED_BASENAMES:
            continue
        if basename not in shared_basenames:
            continue

        # Subclass exemption — only if EVERY simulator file with this
        # basename can be shown to subclass one of the shared classes
        # of the matching basename, the collision is forgiven.
        shared_files = [p for p in _SHARED_OBS_ROOT.rglob(basename) if "__pycache__" not in p.parts]
        expected_class_names: set[str] = set()
        for shared_file in shared_files:
            expected_class_names.update(_shared_class_names(shared_file))

        all_exempt = all(_simulator_file_subclasses_any(sim_path, expected_class_names) for sim_path in sim_paths)
        if not all_exempt:
            collisions.append((basename, sim_paths))

    assert not collisions, (
        "Mirror detection: simulator file basenames collide with "
        "shared/agent_observability basenames without subclass exemption. "
        "Per .claude/rules/anti-duplication.md §0, EXTEND via subclass "
        "or LIFT-TO-SHARED. Collisions:\n"
        + "\n".join(f"  - {basename!r}: {[str(p) for p in paths]}" for basename, paths in collisions)
    )


# ════════════════════════════════════════════════════════════════════════
# Specific cement — high-value basename probes
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "forbidden_basename",
    [
        "turn_envelope.py",
        "base_callback_handler.py",
        "sanitization.py",
        "fx_resolver.py",
        "cost_recorder.py",
        "calculator.py",
        "pricing_resolver.py",
        "base_trace_event_repo.py",
        "base_llm_call_repo.py",
        "tenant_billing_config_repository.py",
        "format_for_channel.py",
        "intent_detector.py",
        "registry.py",
    ],
)
def test_forbidden_basename_not_under_simulator(forbidden_basename: str) -> None:
    """Probe specific basenames that MUST never appear under ``simulator/``.

    These are the canonical shared abstractions (``anti-duplication.md``
    inventory). Even with a subclass-exemption clause, none of these
    SHOULD ever land in the simulator tree — the subclasses live under
    different basenames (``observability.py`` / ``customer_node.py`` /
    etc.).
    """
    matches = [p for p in _SIMULATOR_ROOT.rglob(forbidden_basename) if "__pycache__" not in p.parts]
    assert not matches, (
        f"Forbidden mirror file detected: {forbidden_basename} found at "
        f"{[str(p) for p in matches]}. Per .claude/rules/anti-duplication.md "
        f"§0, EXTEND via subclass under a different basename or LIFT-TO-SHARED."
    )
