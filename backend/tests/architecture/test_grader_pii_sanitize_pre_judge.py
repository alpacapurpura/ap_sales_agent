"""Architecture fitness gate — PII sanitisation pre-judge cement (T-7 / D10).

Story E (sales-agent-voice-fidelity-grader-runtime) D10 cement:
``grade_transcript_maj_eval`` MUST call ``sanitize_payload`` over each transcript
turn BEFORE any judge invocation. Defense-in-depth even on synthetic data
(no whitelist — D10 cement).

Static AST scan strategy
========================

Scan ``grader/_internal/maj_eval.py`` for:

1. An ``import`` statement bringing ``sanitize_payload`` into scope from
   ``src.shared.agent_observability.recording.sanitization`` (or alias).
2. A ``Call`` node referencing ``sanitize_payload`` somewhere inside the body
   of ``grade_transcript_maj_eval``.

Tolerance: ``maj_eval.py`` is a T-5 deliverable. If the file does not yet
exist (T-5 not landed), this gate **xfails with reason** so it does not block
T-7 ship. Once T-5 lands the file, the gate becomes enforcing.

Allowlist: empty (shrink-only ratchet).

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval

# Repo root anchor — `backend/` two levels up from this test file.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_MAJ_EVAL_PATH: Path = (
    _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "grader" / "_internal" / "maj_eval.py"
)


def _maj_eval_present() -> bool:
    """True iff ``maj_eval.py`` is on disk (T-5 deliverable shipped)."""
    return _MAJ_EVAL_PATH.is_file()


def _imports_sanitize_payload(tree: ast.AST) -> bool:
    """Return True iff the AST imports ``sanitize_payload`` from any module."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "sanitize_payload":
                    return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("sanitize_payload"):
                    return True
    return False


def _grade_function_calls_sanitize_payload(tree: ast.AST) -> bool:
    """Scan for ``grade_transcript_maj_eval`` body invoking ``sanitize_payload``."""
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            if node.name != "grade_transcript_maj_eval":
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Name) and func.id == "sanitize_payload":
                        return True
                    if isinstance(func, ast.Attribute) and func.attr == "sanitize_payload":
                        return True
    return False


def test_maj_eval_imports_sanitize_payload() -> None:
    """``maj_eval.py`` imports ``sanitize_payload`` (D10 cement).

    Skips with reason if T-5 hasn't shipped maj_eval.py yet. Becomes enforcing
    once the file exists.
    """
    if not _maj_eval_present():
        pytest.skip(f"{_MAJ_EVAL_PATH} not yet shipped (T-5 deliverable). Gate becomes enforcing post T-5 ship.")
    source = _MAJ_EVAL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert _imports_sanitize_payload(tree), (
        f"{_MAJ_EVAL_PATH} MUST import `sanitize_payload` from "
        f"src.shared.agent_observability.recording.sanitization (D10 cement)."
    )


def test_grade_transcript_maj_eval_calls_sanitize_payload() -> None:
    """``grade_transcript_maj_eval`` invokes ``sanitize_payload`` in its body.

    D10 cement — defense-in-depth even with synthetic eval data. Skips with
    reason if T-5 hasn't shipped maj_eval.py yet.
    """
    if not _maj_eval_present():
        pytest.skip(f"{_MAJ_EVAL_PATH} not yet shipped (T-5 deliverable). Gate becomes enforcing post T-5 ship.")
    source = _MAJ_EVAL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert _grade_function_calls_sanitize_payload(tree), (
        "`grade_transcript_maj_eval` body MUST invoke `sanitize_payload` over the "
        "transcript before any judge call (D10 cement — defense-in-depth)."
    )
