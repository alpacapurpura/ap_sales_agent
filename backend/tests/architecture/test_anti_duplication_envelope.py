"""Anti-duplication ratchet for envelope + FX subsystems (PR-2 PI-1.1).

Origen: PR-1 PI-1.1 hotfix 2026-05-01 — builder agentic created
``modules/sales_agent/observability/recording/turn_envelope.py`` mirror
of ``modules/copilot/observability/recording/turn_envelope.py``. REVERT
obligatorio. This PR is the FIRST TEST of the 5-layer anti-duplication
enforcement. Layer 3 (auditor Cat 12 mirror detection) + Layer 4 (this
arch test) ensure regressions never re-land.

Five invariants:

1. ``turn_envelope.py`` exists ONLY at canonical 3-file set: shared
   base + 2 concrete subclasses (copilot, sales_agent).
2. ``BaseObservabilityContext`` defined ONLY at the shared canonical
   path; ``CopilotObservabilityContext`` only in copilot;
   ``SalesAgentObservabilityContext`` only in sales_agent.
3. Concrete subclasses do NOT redefine locked lifecycle methods
   (AST scan).
4. No ``FXResolver()`` no-arg call site anywhere in ``backend/src/``
   — Bug #8 regression guard.
5. No ``lambda: httpx.Client(timeout=10)`` literal pattern outside
   ``FXResolver.default()`` — anti-mirror guard.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"

CANONICAL_ENVELOPE_FILES = {
    SRC / "shared" / "agent_observability" / "recording" / "turn_envelope.py",
    SRC / "modules" / "copilot" / "observability" / "recording" / "turn_envelope.py",
    SRC / "modules" / "sales_agent" / "observability" / "recording" / "turn_envelope.py",
}

LOCKED_LIFECYCLE_METHODS = frozenset(
    {
        "observe_turn",
        "langchain_config",
        "set_turn_summary",
        "set_turn_error",
        "_write_turn_start",
        "_write_turn_end",
        "_commit_session",
        "_safe_aggregate_totals",
        "_safe_legacy_compat_keys",
    },
)


def _is_real_source(p: Path) -> bool:
    s = str(p)
    return "site-packages" not in s and "__pycache__" not in s and ".venv" not in s


def test_no_parallel_turn_envelope_files_outside_canonical() -> None:
    """Only the canonical 3 paths may host ``turn_envelope.py``."""
    found = {p for p in SRC.rglob("turn_envelope.py") if _is_real_source(p)}
    extras = found - CANONICAL_ENVELOPE_FILES
    missing = CANONICAL_ENVELOPE_FILES - found
    assert not extras, f"Parallel envelope files outside canonical set: {extras}"
    assert not missing, f"Missing canonical envelope file: {missing}"


def test_envelope_class_definitions_only_in_canonical_files() -> None:
    """``BaseObservabilityContext`` / ``CopilotObservabilityContext`` /
    ``SalesAgentObservabilityContext`` defined only at canonical paths.

    Catches accidental class re-definitions (mirror anti-pattern).
    Module-level alias ``ObservabilityContext = CopilotObservabilityContext``
    does NOT count as a class definition.
    """
    forbidden_class_names = {
        "BaseObservabilityContext": SRC / "shared" / "agent_observability" / "recording" / "turn_envelope.py",
        "CopilotObservabilityContext": SRC / "modules" / "copilot" / "observability" / "recording" / "turn_envelope.py",
        "SalesAgentObservabilityContext": SRC
        / "modules"
        / "sales_agent"
        / "observability"
        / "recording"
        / "turn_envelope.py",
    }
    violations: list[str] = []

    for py in SRC.rglob("*.py"):
        if not _is_real_source(py):
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name in forbidden_class_names:
                expected = forbidden_class_names[node.name]
                if py != expected:
                    violations.append(f"{py.relative_to(REPO)}: redefines class {node.name}")

    assert not violations, "Anti-duplication mirror detected:\n" + "\n".join(violations)


def test_concrete_subclasses_do_not_override_locked_methods() -> None:
    """Lifecycle is owned by the base; subclasses MUST NOT shadow it."""
    subclass_files = {
        "CopilotObservabilityContext": SRC / "modules" / "copilot" / "observability" / "recording" / "turn_envelope.py",
        "SalesAgentObservabilityContext": SRC
        / "modules"
        / "sales_agent"
        / "observability"
        / "recording"
        / "turn_envelope.py",
    }
    violations: list[str] = []

    for class_name, path in subclass_files.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        target_class: ast.ClassDef | None = next(
            (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name),
            None,
        )
        assert target_class is not None, f"{class_name} not found in {path}"
        own_methods = {b.name for b in target_class.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))}
        overridden = own_methods & LOCKED_LIFECYCLE_METHODS
        if overridden:
            violations.append(f"{class_name} overrides locked methods: {overridden}")

    assert not violations, "\n".join(violations)


def test_no_no_arg_fxresolver_calls_in_src() -> None:
    """Bug #8 regression guard: ``FXResolver()`` (no args) is forbidden.

    Only ``FXResolver.default()`` (production) and
    ``FXResolver(http_client_factory=...)`` (tests with explicit mock /
    real factory) are permitted. The class definition itself is
    excluded.
    """
    pattern = re.compile(r"\bFXResolver\(\s*\)")
    violations: list[str] = []

    for py in SRC.rglob("*.py"):
        if not _is_real_source(py):
            continue
        text = py.read_text(encoding="utf-8")
        # Skip the class definition file itself (it contains the dataclass def).
        if py.name == "fx_resolver.py":
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            # Skip comments / docstring lines that mention the pattern descriptively.
            stripped = line.lstrip()
            if stripped.startswith(("#", '"""', "'''")):
                continue
            if pattern.search(line):
                violations.append(f"{py.relative_to(REPO)}:{lineno}: {line.strip()}")

    assert not violations, "Bug #8 regression — ``FXResolver()`` no-arg detected:\n" + "\n".join(violations)


def test_no_inline_httpx_client_factory_lambda_outside_default() -> None:
    """Anti-mirror guard: the encapsulated boilerplate must live only
    inside ``FXResolver.default()``. Other call sites use the factory.
    """
    pattern = re.compile(r"lambda:\s*httpx\.Client\(\s*timeout\s*=")
    violations: list[str] = []

    for py in SRC.rglob("*.py"):
        if not _is_real_source(py):
            continue
        # ``fx_resolver.py`` itself defines the factory and may contain the lambda.
        if py.name == "fx_resolver.py":
            continue
        text = py.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                violations.append(f"{py.relative_to(REPO)}:{lineno}: {line.strip()}")

    assert not violations, "Anti-mirror — duplicated httpx client factory lambda:\n" + "\n".join(violations)
