"""Architecture fitness gate — sandbox markers literal cement (T-7 / DQ2).

Story E (sales-agent-voice-fidelity-grader-runtime) defense-in-depth layer 2:
``grader/_internal/judge_prompts.py`` MUST emit the literal sandbox marker
strings ``<<TRANSCRIPT_BEGIN>>`` and ``<<TRANSCRIPT_END>>`` inside the body of
the function/code path that wraps transcript content (Slot 5 builder).

The literals MUST be **inline string constants** — parametrized markers (variable
names, format placeholders) defeat the sandbox contract because a future
refactor could replace them silently. Static AST scan asserts the exact
strings appear in module-level constants AND inside function bodies that
build prompts.

DQ2 cement layers
=================

1. **Slot 1 system directive** (cacheable TTL=1h) — `CRITICAL SECURITY DIRECTIVE`
   block references the markers verbatim.
2. **Slot 5 prompt builder** (this gate) — literal markers wrap transcript content.
3. **Arch fitness gate** (this file) — static AST scan enforces #1 + #2.

Allowlist: empty (shrink-only ratchet). Any drift fails the gate.

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

_MARKER_BEGIN: str = "<<TRANSCRIPT_BEGIN>>"
_MARKER_END: str = "<<TRANSCRIPT_END>>"


def _collect_string_constants(tree: ast.AST) -> list[str]:
    """Collect every ``str`` constant node value in the AST.

    Handles both legacy ``ast.Str`` and modern ``ast.Constant`` nodes. Used to
    verify the markers appear as inline string constants (not parametrized).
    """
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def test_judge_prompts_module_exists() -> None:
    """Sanity — judge_prompts.py is on disk (T-7 deliverable shipped)."""
    assert _JUDGE_PROMPTS_PATH.is_file(), (
        f"Expected judge_prompts.py at {_JUDGE_PROMPTS_PATH}; T-7 deliverable missing."
    )


def test_sandbox_marker_begin_literal_in_judge_prompts() -> None:
    """Literal `<<TRANSCRIPT_BEGIN>>` appears as inline string constant in judge_prompts.py.

    Defense-in-depth layer 2 cement (DQ2). The marker must NOT be parametrized
    or constructed at runtime — it must be an exact inline string literal so
    static analysis (this gate) can assert its presence.
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = _collect_string_constants(tree)
    has_begin = any(_MARKER_BEGIN in c for c in constants)
    assert has_begin, (
        f"Sandbox marker {_MARKER_BEGIN!r} MUST appear as an inline string literal "
        f"in {_JUDGE_PROMPTS_PATH}. DQ2 cement — markers may NOT be parametrized."
    )


def test_sandbox_marker_end_literal_in_judge_prompts() -> None:
    """Literal `<<TRANSCRIPT_END>>` appears as inline string constant in judge_prompts.py.

    Defense-in-depth layer 2 cement (DQ2). Pair with BEGIN marker.
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = _collect_string_constants(tree)
    has_end = any(_MARKER_END in c for c in constants)
    assert has_end, (
        f"Sandbox marker {_MARKER_END!r} MUST appear as an inline string literal "
        f"in {_JUDGE_PROMPTS_PATH}. DQ2 cement — markers may NOT be parametrized."
    )


def test_slot_1_template_references_sandbox_markers() -> None:
    """Slot 1 system directive (DQ2 layer 1 cement) references the literal markers.

    The CRITICAL SECURITY DIRECTIVE block in SLOT_1_TEMPLATE must mention both
    markers verbatim so judges treat content within them as data, not instructions.
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # Find the SLOT_1_TEMPLATE assignment value (handles both Assign and AnnAssign)
    slot_1_value: str | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "SLOT_1_TEMPLATE"
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    slot_1_value = node.value.value
                    break
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "SLOT_1_TEMPLATE"
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            slot_1_value = node.value.value

    assert slot_1_value is not None, (
        f"Module-level constant SLOT_1_TEMPLATE not found (or non-string value) in "
        f"{_JUDGE_PROMPTS_PATH}. DQ2 layer 1 cement requires this constant to exist."
    )
    assert _MARKER_BEGIN in slot_1_value, (
        f"SLOT_1_TEMPLATE must reference {_MARKER_BEGIN!r} verbatim (DQ2 layer 1 cement)."
    )
    assert _MARKER_END in slot_1_value, f"SLOT_1_TEMPLATE must reference {_MARKER_END!r} verbatim (DQ2 layer 1 cement)."


def test_slot_5_builder_emits_literal_markers() -> None:
    """The Slot 5 builder function body contains both literal markers.

    Walk every function in judge_prompts.py and find the one whose body emits
    BOTH markers as string constants (i.e., the ``_build_slot_5`` builder per
    03-arch.md§4.1 reference impl). Asserting at least ONE function in the
    module satisfies this is enough — the gate is defense-in-depth, not
    structural enforcement of a specific function name.
    """
    source = _JUDGE_PROMPTS_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    functions_with_both_markers: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body_constants: list[str] = []
        for sub in ast.walk(node):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                body_constants.append(sub.value)
        has_begin = any(_MARKER_BEGIN in c for c in body_constants)
        has_end = any(_MARKER_END in c for c in body_constants)
        if has_begin and has_end:
            functions_with_both_markers.append(node.name)

    assert functions_with_both_markers, (
        f"At least ONE function in {_JUDGE_PROMPTS_PATH} must emit BOTH "
        f"{_MARKER_BEGIN!r} AND {_MARKER_END!r} as inline literal string constants "
        f"(DQ2 cement — Slot 5 builder defense-in-depth)."
    )
