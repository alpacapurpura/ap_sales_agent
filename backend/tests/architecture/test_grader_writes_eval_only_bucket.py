"""Architecture fitness gate — grader cost-bucket invariant H7 (T-8 / Story E).

Story B (H7) cement extended for Story E:
Judge LLM calls originating in the grader subtree MUST write to
``eval_simulator_llm_call`` ONLY. Zero contamination of production LLM
cost buckets:

* ``copilot_llm_call`` — copilot runtime LLM calls
* ``sales_agent_llm_call`` — sales-agent runtime LLM calls
* ``campaign_llm_call`` — campaigns LLM calls (if enabled)

Cross-cost-bucket writes from grader code = runtime cost rollup
contamination + observability misattribution. Production billing depends
on cost-bucket separation; grader (test-infra) MUST stay out.

Static-analysis approach
========================

The gate parses every ``*.py`` file under the grader subtree and verifies:

1. **No import** of forbidden ORM model classes
   (``CopilotLlmCallModel``, ``SalesAgentLlmCallModel``,
   ``CampaignLlmCallModel``) from any module path.

2. **No string literal** of forbidden table names
   (``"copilot_llm_call"``, ``"sales_agent_llm_call"``,
   ``"campaign_llm_call"``) anywhere in grader source.
   (Docstrings citing the invariant verbatim are allowed via the explicit
   docstring-walk exemption — see ``_extract_string_literals_outside_docstrings``.)

3. **The grader writes to ``eval_simulator_llm_call``** — verified
   indirectly: at least one grader file references
   ``eval_simulator_llm_call`` or imports from
   ``src.modules.sales_agent.observability.eval_simulator.persistence``
   (the canonical write path via observability subclass + cost_recorder).

Pattern precedent: ``test_simulator_writes_eval_kind_tag.py`` (Story B
T-9). Ratchet pattern — empty allowlists shrink-only.

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval


# Repo root anchor — `backend/` two levels up from this test file.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_GRADER_ROOT: Path = _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "grader"


# Forbidden ORM model class names — production cost buckets.
_FORBIDDEN_MODEL_CLASSES: frozenset[str] = frozenset(
    {
        "CopilotLlmCallModel",
        "SalesAgentLlmCallModel",
        "CampaignLlmCallModel",
    },
)

# Forbidden SQL table names — production cost buckets.
_FORBIDDEN_TABLE_LITERALS: frozenset[str] = frozenset(
    {
        "copilot_llm_call",
        "sales_agent_llm_call",
        "campaign_llm_call",
    },
)

# Canonical eval write path indicators — at least one file in grader/
# MUST reference one of these (sanity check that the grader actually
# writes somewhere — not a no-op).
_CANONICAL_EVAL_WRITE_INDICATORS: frozenset[str] = frozenset(
    {
        "eval_simulator_llm_call",
        "EvalSimulatorLlmCallModel",
        "src.modules.sales_agent.observability.eval_simulator.persistence",
    },
)


def _walk_grader_python_files(root: Path) -> list[Path]:
    """Return ``*.py`` files under ``root`` (excluding ``__pycache__``)."""
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _parse_or_skip(path: Path) -> ast.Module | None:
    """Parse a Python file and return its AST module node, or None on failure."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None


def _extract_imported_names(tree: ast.Module) -> set[str]:
    """Collect every name imported by ``import X`` and ``from X import Y``.

    Returns the set of bound local names + the dotted module paths in scope.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module_path = node.module or ""
            names.add(module_path)
            for alias in node.names:
                names.add(alias.name)
                names.add(alias.asname or alias.name)
    return names


def _extract_string_literals_outside_docstrings(tree: ast.Module) -> set[str]:
    """Walk the AST and collect string literal values.

    Excludes module-level / class-level / function-level docstrings (the
    leading ``Expr(Constant(str))`` of each scoped body). Citations of the
    cost-bucket invariant in docstrings are allowed; only EXECUTABLE code
    referencing forbidden table names triggers the gate.
    """
    docstring_node_ids: set[int] = set()

    def _mark_docstring(scope_body: list[ast.stmt]) -> None:
        if not scope_body:
            return
        first = scope_body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            docstring_node_ids.add(id(first.value))

    _mark_docstring(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _mark_docstring(node.body)

    literals: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in docstring_node_ids:
                continue
            literals.add(node.value)
    return literals


# ════════════════════════════════════════════════════════════════════════
# Smoke + path existence
# ════════════════════════════════════════════════════════════════════════


def test_grader_root_exists() -> None:
    """Sanity — grader package exists post T-2..T-8 builds."""
    assert _GRADER_ROOT.is_dir(), f"Grader package root not found at {_GRADER_ROOT}; T-2..T-8 deliverables missing."


def test_grader_has_python_files() -> None:
    """Sanity — grader subtree contains at least one Python file (not empty)."""
    files = _walk_grader_python_files(_GRADER_ROOT)
    assert files, f"No *.py files under {_GRADER_ROOT} — gate would pass vacuously."


# ════════════════════════════════════════════════════════════════════════
# Forbidden ORM model class imports — main invariant H7
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("forbidden_class", sorted(_FORBIDDEN_MODEL_CLASSES))
def test_no_forbidden_orm_class_imported(forbidden_class: str) -> None:
    """Cero grader file imports a production cost-bucket ORM model class.

    Importing ``CopilotLlmCallModel`` / ``SalesAgentLlmCallModel`` /
    ``CampaignLlmCallModel`` from grader code would let a developer write
    rows into prod cost buckets — H7 cement violation.
    """
    offending: list[Path] = []
    for path in _walk_grader_python_files(_GRADER_ROOT):
        tree = _parse_or_skip(path)
        if tree is None:
            continue
        imported = _extract_imported_names(tree)
        if forbidden_class in imported:
            offending.append(path)

    assert not offending, (
        f"Forbidden ORM model class {forbidden_class!r} imported in grader code. "
        f"Cost-bucket invariant H7 violated — judge LLM calls MUST write to "
        f"eval_simulator_llm_call ONLY. Offending files:\n" + "\n".join(f"  - {p}" for p in offending)
    )


@pytest.mark.parametrize("forbidden_table", sorted(_FORBIDDEN_TABLE_LITERALS))
def test_no_forbidden_table_literal_in_executable_code(forbidden_table: str) -> None:
    """Cero string literal references a production cost-bucket table name.

    Grader source MAY mention the table names in docstrings (citing the
    invariant) but EXECUTABLE code paths (raw SQL, table assertions,
    ORM ``__tablename__`` overrides) MUST NOT reference them.

    Implementation: walk AST, collect string constants, exclude scope-level
    docstrings, then check for forbidden literals.
    """
    offending: list[tuple[Path, str]] = []
    for path in _walk_grader_python_files(_GRADER_ROOT):
        tree = _parse_or_skip(path)
        if tree is None:
            continue
        literals = _extract_string_literals_outside_docstrings(tree)
        for lit in literals:
            if forbidden_table in lit:
                offending.append((path, lit))

    assert not offending, (
        f"Forbidden table name literal {forbidden_table!r} found in grader "
        f"executable code (outside docstrings). Cost-bucket invariant H7 "
        f"violated. Offending files + literals:\n" + "\n".join(f"  - {p}: {literal!r}" for p, literal in offending)
    )


# ════════════════════════════════════════════════════════════════════════
# Canonical eval write path — sanity (grader actually writes to eval bucket)
# ════════════════════════════════════════════════════════════════════════


def test_grader_references_canonical_eval_write_path() -> None:
    """At least one grader file MUST reference the canonical eval write path.

    Sanity check: if grader code writes nowhere, the cost-bucket invariant
    is vacuous. This test ensures grader actively references
    ``eval_simulator_llm_call`` (table) or
    ``EvalSimulatorLlmCallModel`` (ORM) or the
    ``modules.sales_agent.observability.eval_simulator.persistence`` path
    in at least one file (across imports + string literals).
    """
    found_indicators: set[str] = set()
    for path in _walk_grader_python_files(_GRADER_ROOT):
        tree = _parse_or_skip(path)
        if tree is None:
            continue

        imported = _extract_imported_names(tree)
        for indicator in _CANONICAL_EVAL_WRITE_INDICATORS:
            for name in imported:
                if indicator in name:
                    found_indicators.add(indicator)

        # Scan string literals (table name references in docstrings allowed
        # for sanity since the docstring referencing eval_simulator_llm_call
        # is structural evidence).
        text = path.read_text(encoding="utf-8")
        for indicator in _CANONICAL_EVAL_WRITE_INDICATORS:
            if indicator in text:
                found_indicators.add(indicator)

    assert found_indicators, (
        f"Cost-bucket sanity check failed: NO grader file references any of "
        f"{sorted(_CANONICAL_EVAL_WRITE_INDICATORS)}. Either grader writes "
        f"NOWHERE (test-only no-op) or it writes to a non-canonical path. "
        f"Verify judge_registry.py + maj_eval.py emit eval_simulator_llm_call "
        f"rows via the observability subclass + cost_recorder bridge."
    )
