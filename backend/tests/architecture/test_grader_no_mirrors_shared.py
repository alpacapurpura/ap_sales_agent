"""Architecture fitness gate — grader anti-mirror cement (T-7 / anti-duplication).

Story E (sales-agent-voice-fidelity-grader-runtime) cement:
NO file under ``backend/tests/agentic_evals/sales_agent/grader/`` (or its
``_internal/`` subpackage) may duplicate the *basename* of a file that already
exists under ``backend/src/shared/agent_observability/``.

Pattern precedent: ``test_simulator_no_mirrors_shared.py`` (Story B T-9).
This gate enforces the same invariant on the grader subtree, where Story E
introduces NEW files that must REUSE shared abstractions (cost_recorder,
sanitization, callback handlers, FX/pricing resolvers) — never mirror.

Subclass exemption
==================

A grader file MAY share a basename with a shared file IF AND ONLY IF:

* It is ``__init__.py`` (allowed everywhere — namespace marker), OR
* It declares at least one class that subclasses a class defined in the
  matching shared file.

Allowlists are intentionally absent — any drift fails the gate.

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
_GRADER_ROOT: Path = _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "grader"

# Always-allowed basenames (namespace markers, no logic).
_ALLOWED_BASENAMES: frozenset[str] = frozenset({"__init__.py"})


def _walk_python_basenames(root: Path) -> dict[str, list[Path]]:
    """Return a basename → list[absolute path] map for ``*.py`` under ``root``.

    A basename appearing more than once across the tree (e.g. ``__init__.py``)
    maps to multiple paths.
    """
    out: dict[str, list[Path]] = {}
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        out.setdefault(p.name, []).append(p)
    return out


def _shared_class_names(shared_path: Path) -> set[str]:
    """Parse a shared file and collect top-level class names."""
    try:
        tree = ast.parse(shared_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _grader_file_subclasses_any(grader_path: Path, expected: set[str]) -> bool:
    """Return True iff ``grader_path`` defines a class extending one of ``expected``."""
    try:
        tree = ast.parse(grader_path.read_text(encoding="utf-8"))
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
        "repo layout drift detected — update this gate."
    )


def test_grader_root_exists() -> None:
    """Sanity — grader package exists post T-2..T-9 builds."""
    assert _GRADER_ROOT.is_dir(), f"Grader package root not found at {_GRADER_ROOT}; T-2..T-9 deliverables missing."


# ════════════════════════════════════════════════════════════════════════
# Basename collision detection — main invariant (no allowlist)
# ════════════════════════════════════════════════════════════════════════


def test_no_basename_collision_with_shared_observability() -> None:
    """Cero grader basename ∈ shared/agent_observability basenames.

    REUSE shared abstractions via canonical imports; do not co-locate
    same-basename files under grader/. Subclass exemption documented above
    is intentionally narrow — only ``__init__.py`` is unconditionally allowed.
    """
    shared_basenames = set(_walk_python_basenames(_SHARED_OBS_ROOT))
    grader_basenames = _walk_python_basenames(_GRADER_ROOT)

    collisions: list[tuple[str, list[Path]]] = []
    for basename, grader_paths in grader_basenames.items():
        if basename in _ALLOWED_BASENAMES:
            continue
        if basename not in shared_basenames:
            continue

        # Subclass exemption — only if EVERY grader file with this basename can
        # be shown to subclass one of the shared classes of the matching basename
        # is the collision forgiven.
        shared_files = [p for p in _SHARED_OBS_ROOT.rglob(basename) if "__pycache__" not in p.parts]
        expected_class_names: set[str] = set()
        for shared_file in shared_files:
            expected_class_names.update(_shared_class_names(shared_file))

        all_exempt = all(_grader_file_subclasses_any(gp, expected_class_names) for gp in grader_paths)
        if not all_exempt:
            collisions.append((basename, grader_paths))

    assert not collisions, (
        "Mirror detection: grader file basenames collide with "
        "shared/agent_observability basenames without subclass exemption. "
        "Per .claude/rules/anti-duplication.md §0, REUSE the canonical shared "
        "module via import, or EXTEND via subclass under a DIFFERENT basename. "
        "Collisions:\n" + "\n".join(f"  - {basename!r}: {[str(p) for p in paths]}" for basename, paths in collisions)
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
def test_forbidden_basename_not_under_grader(forbidden_basename: str) -> None:
    """Probe specific basenames that MUST never appear under ``grader/``.

    These are the canonical shared abstractions per
    ``.claude/rules/anti-duplication.md`` inventory. None of them should land
    in the grader tree — REUSE via canonical import path.
    """
    matches = [p for p in _GRADER_ROOT.rglob(forbidden_basename) if "__pycache__" not in p.parts]
    assert not matches, (
        f"Forbidden mirror file detected: {forbidden_basename} found at "
        f"{[str(p) for p in matches]}. Per .claude/rules/anti-duplication.md §0, "
        f"REUSE the canonical shared module via import (no mirror under grader/)."
    )
