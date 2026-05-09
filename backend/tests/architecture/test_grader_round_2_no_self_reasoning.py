"""Architecture fitness gate — Round 2 anti-anchoring cement (T-7 / DQ3).

Story E (sales-agent-voice-fidelity-grader-runtime) DQ3 cement:
the Round 2 prompt builder for judge X MUST inject reasoning ONLY from the
OTHER 2 peers — NEVER X's own R1 reasoning. Self-reflection in Round 2 is the
canonical anchoring trap (MoA-Judge research, post-cutoff April 2026).

Static AST scan strategy
========================

The Round 2 peer-reasoning logic in ``judge_prompts.py`` MUST contain a filter
expression that drops entries where the iterated ``judge_id`` equals the input
``judge_id`` parameter. Concretely we look for either:

* an ``ast.Compare`` node with operator ``ast.NotEq`` between two name nodes
  whose names involve ``judge_id`` (e.g., ``jid != judge_id``), OR
* an ``if`` statement guarding peer-reasoning emission with the same comparison.

If neither pattern is found in the module's AST, the gate fails. Allowlist:
empty (shrink-only ratchet).

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval

# Repo root anchor — `backend/` two levels up from this test file.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_JUDGE_PROMPTS_PATH: Path = (
    _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "grader" / "_internal" / "judge_prompts.py"
)


def _name_carries_judge_id(name: str) -> bool:
    """Return True if a name token plausibly refers to a per-iteration judge id."""
    return name in {"judge_id", "jid", "j_id", "peer_judge_id", "peer_id"}


def _has_judge_id_inequality(tree: ast.AST) -> bool:
    """Walk the AST and look for ``judge_id``-related ``!=`` comparisons.

    Matches expressions of the form ``X != Y`` (or ``X is not Y``) where at
    least one side is a Name whose identifier looks like a judge id. This is
    intentionally permissive — multiple builder structures satisfy the
    contract; we only enforce that SOME inequality is present in the AST.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        # Compare nodes can have multiple ops + comparators; we scan all pairs.
        if not node.ops or not node.comparators:
            continue
        for op, right in zip(node.ops, node.comparators, strict=False):
            if not isinstance(op, ast.NotEq | ast.IsNot):
                continue
            left_name = node.left.id if isinstance(node.left, ast.Name) else None
            right_name = right.id if isinstance(right, ast.Name) else None
            if (left_name and _name_carries_judge_id(left_name)) or (right_name and _name_carries_judge_id(right_name)):
                return True
    return False


def test_judge_prompts_module_exists() -> None:
    """Sanity — judge_prompts.py is on disk (T-7 deliverable)."""
    assert _JUDGE_PROMPTS_PATH.is_file(), (
        f"Expected judge_prompts.py at {_JUDGE_PROMPTS_PATH}; T-7 deliverable missing."
    )


def test_round_2_peer_filter_judge_id_inequality_present() -> None:
    """AST contains a ``judge_id`` inequality — DQ3 anti-anchoring filter cement.

    The Round 2 builder MUST drop any peer-reasoning entry whose ``judge_id``
    matches the input ``judge_id`` parameter. The static scan looks for any
    ``!=`` (or ``is not``) comparison whose name tokens look like judge ids.
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert _has_judge_id_inequality(tree), (
        "judge_prompts.py AST does not contain a `judge_id` inequality filter. "
        "Round 2 builder MUST drop peer-reasoning entries where the iterated "
        "judge_id equals the input judge_id parameter (DQ3 anti-anchoring cement). "
        "Expected pattern: `[(jid, sc, rsn) for (jid, sc, rsn) in peer_reasoning if jid != judge_id]` "
        "or equivalent."
    )


def test_round_2_peer_open_marker_constant_present() -> None:
    """The Round 2 peer-reasoning block opener literal is present.

    Marker `<<ROUND_2_PEER_REASONING>>` is the cement structural anchor that
    differentiates Round 2 from Round 1 (Round 1 builders MUST NOT emit it).
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants: list[str] = [
        node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    has_marker = any("<<ROUND_2_PEER_REASONING>>" in c for c in constants)
    assert has_marker, (
        "judge_prompts.py must contain literal `<<ROUND_2_PEER_REASONING>>` "
        "structural marker for Round 2 peer reasoning block (DQ3 cement)."
    )


def test_round_2_peer_close_marker_constant_present() -> None:
    """The Round 2 peer-reasoning block closer literal is present."""
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants: list[str] = [
        node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    has_marker = any("<<ROUND_2_PEER_REASONING_END>>" in c for c in constants)
    assert has_marker, (
        "judge_prompts.py must contain literal `<<ROUND_2_PEER_REASONING_END>>` "
        "structural marker for Round 2 peer reasoning block close (DQ3 cement)."
    )


def test_round_2_peer_filter_round_n_guard_present() -> None:
    """The Round 2 builder is guarded by an ``if`` checking ``round_n == 2``.

    Round 1 builders MUST NOT emit peer-reasoning blocks. The static scan
    looks for any equality test against the literal int ``2`` involving a
    ``round`` token.
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    has_round_2_guard = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not isinstance(node.left, ast.Name):
            continue
        if "round" not in node.left.id.lower():
            continue
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            if isinstance(op, ast.Eq) and isinstance(comparator, ast.Constant) and comparator.value == 2:
                has_round_2_guard = True
                break
        if has_round_2_guard:
            break
    assert has_round_2_guard, (
        "Round 2 prompt assembly MUST be guarded by `round_n == 2` equality check "
        "(DQ3 cement — Round 1 builders must not emit peer-reasoning blocks)."
    )
