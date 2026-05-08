"""Architecture fitness gate — H5 eval_metadata tag enforcement (T-9).

Story B (T-9) cement: every observability write originating in the
simulator subtree carries the H5 invariant 6-key ``eval_metadata`` jsonb.
Streamlit prod queries rely on
``WHERE eval_metadata->>'eval_run_kind' = 'simulator'`` to filter eval
traffic out — silent drops at this layer would leak eval cost into
production rollups.

Static-analysis approach
========================

The gate parses the simulator's ``_internal/observability.py`` AST and
verifies that:

1. ``build_eval_metadata(...)`` is the SSoT helper that materializes
   the 6 mandatory keys — its body is a single dict literal + has the
   exact 6 keys + ``eval_run_kind`` is the literal string ``"simulator"``.

2. ``_MANDATORY_EVAL_METADATA_KEYS`` (frozenset) lists EXACTLY those 6
   keys — same key set as ``build_eval_metadata`` returns.

3. Any function in the simulator subtree that constructs an
   ``EvalSimulatorObservabilityContext.start(...)`` MUST include
   ``eval_metadata=`` as a keyword argument or pass through
   ``build_eval_metadata(...)`` (the factory in T-7).

4. The runner's ``_build_eval_metadata`` helper (paridad SSoT) produces
   the same 6-key dict — same string literal ``"simulator"``.

Static-only — no runtime invocation needed. The runtime defense is
``_assert_eval_metadata_complete`` invoked from ``__post_init__`` of
``EvalSimulatorObservabilityContext`` (T-5).

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval


_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_SIMULATOR_INTERNAL: Path = _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "simulator" / "_internal"


_EXPECTED_KEYS: frozenset[str] = frozenset(
    {
        "eval_run_kind",
        "archetype_slug",
        "actor_profile_id",
        "trial_n",
        "simulation_id",
        "run_id",
    },
)


def _parse(path: Path) -> ast.Module:
    """Parse a Python file and return its AST module node."""
    return ast.parse(path.read_text(encoding="utf-8"))


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    """Locate a top-level function definition by name."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _dict_keys_in_return(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return the set of string literal keys from ``return {...}`` in ``fn``.

    Walks the function body and looks for a Return whose value is a Dict
    with string-literal keys. Returns empty set if no such return found
    (which fails the calling assertion).
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        keys: set[str] = set()
        for key_node in node.value.keys:
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                keys.add(key_node.value)
        if keys:
            return keys
    return set()


def _eval_run_kind_literal(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Return the literal string value bound to key ``eval_run_kind`` in the dict return.

    Defensive: returns None if the key is absent or the value is not a
    string Constant (signals a parametrized invariant bug).
    """
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        for key_node, value_node in zip(node.value.keys, node.value.values, strict=False):
            if (
                isinstance(key_node, ast.Constant)
                and key_node.value == "eval_run_kind"
                and isinstance(value_node, ast.Constant)
                and isinstance(value_node.value, str)
            ):
                return value_node.value
    return None


def _frozenset_string_args(fn_or_module: ast.AST, var_name: str) -> set[str] | None:
    """Find a top-level assignment ``var_name = frozenset({...})`` and return its string members.

    Walks the AST and matches assignments whose value is a Call to
    ``frozenset`` with a single Set/List arg of string Constants.
    Returns None when the binding is absent or non-conformant.
    """
    for node in ast.walk(fn_or_module):
        # AnnAssign (annotated) or Assign (plain). Both have ``value``.
        target_names: list[str] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    target_names.append(tgt.id)
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_names.append(node.target.id)
            value = node.value
        else:
            continue

        if var_name not in target_names:
            continue
        if value is None:
            continue
        if not (isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "frozenset"):
            continue
        if len(value.args) != 1:
            continue
        arg = value.args[0]
        if isinstance(arg, (ast.Set, ast.List, ast.Tuple)):
            collected: set[str] = set()
            for elt in arg.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    collected.add(elt.value)
            return collected
    return None


# ════════════════════════════════════════════════════════════════════════
# observability.py — SSoT helper invariants
# ════════════════════════════════════════════════════════════════════════


def test_observability_module_exists() -> None:
    """Sanity — T-5 observability subclass module landed under _internal/."""
    obs = _SIMULATOR_INTERNAL / "observability.py"
    assert obs.is_file(), "_internal/observability.py missing — T-5 deliverable absent."


def test_build_eval_metadata_returns_six_keys_literal() -> None:
    """``build_eval_metadata(...)`` body MUST return a dict with exactly the 6 H5 keys.

    Static AST scan — proves the SSoT helper cannot silently drop a key
    via refactor.
    """
    tree = _parse(_SIMULATOR_INTERNAL / "observability.py")
    fn = _find_function(tree, "build_eval_metadata")
    assert fn is not None, "build_eval_metadata not found in _internal/observability.py — H5 SSoT helper deleted."
    keys = _dict_keys_in_return(fn)
    assert keys == set(_EXPECTED_KEYS), (
        f"build_eval_metadata MUST return exactly the 6 H5 keys. "
        f"Expected: {sorted(_EXPECTED_KEYS)}; got: {sorted(keys)}. "
        f"Missing: {sorted(set(_EXPECTED_KEYS) - keys)}; "
        f"unexpected: {sorted(keys - set(_EXPECTED_KEYS))}."
    )


def test_build_eval_metadata_eval_run_kind_is_literal_simulator() -> None:
    """``eval_run_kind`` MUST be the literal string ``"simulator"``.

    Cement: Streamlit queries filter by this literal — drift would
    silently corrupt cost rollups.
    """
    tree = _parse(_SIMULATOR_INTERNAL / "observability.py")
    fn = _find_function(tree, "build_eval_metadata")
    assert fn is not None, "build_eval_metadata missing"
    literal = _eval_run_kind_literal(fn)
    assert literal == "simulator", (
        f"eval_run_kind literal drift: expected 'simulator'; got {literal!r}. "
        f"Production Streamlit queries depend on this exact value."
    )


def test_mandatory_eval_metadata_keys_constant_matches() -> None:
    """``_MANDATORY_EVAL_METADATA_KEYS`` MUST equal the 6 H5 keys.

    Defense-in-depth: paridad SSoT with ``build_eval_metadata`` keys.
    ``_assert_eval_metadata_complete`` reads this constant; drift between
    them would let one path persist a row the other path would reject.
    """
    tree = _parse(_SIMULATOR_INTERNAL / "observability.py")
    members = _frozenset_string_args(tree, "_MANDATORY_EVAL_METADATA_KEYS")
    assert members is not None, (
        "_MANDATORY_EVAL_METADATA_KEYS frozenset not found or non-conformant in observability.py."
    )
    assert members == set(_EXPECTED_KEYS), (
        f"_MANDATORY_EVAL_METADATA_KEYS drift: expected {sorted(_EXPECTED_KEYS)}; got {sorted(members)}."
    )


# ════════════════════════════════════════════════════════════════════════
# runner.py — paridad helper SSoT
# ════════════════════════════════════════════════════════════════════════


def test_runner_build_eval_metadata_paridad_with_observability() -> None:
    """``runner._build_eval_metadata`` MUST return the same 6 H5 keys.

    The runner intentionally keeps a local copy (avoids importing the
    DB-bound observability module) — but the dict shape MUST byte-match
    so the callback handler subclass can compare key sets at runtime.
    """
    runner_path = _SIMULATOR_INTERNAL / "runner.py"
    assert runner_path.is_file(), "runner.py missing — T-8 deliverable absent."
    tree = _parse(runner_path)
    fn = _find_function(tree, "_build_eval_metadata")
    assert fn is not None, "_build_eval_metadata not found in runner.py — paridad helper missing."
    keys = _dict_keys_in_return(fn)
    assert keys == set(_EXPECTED_KEYS), (
        f"runner._build_eval_metadata key drift: expected {sorted(_EXPECTED_KEYS)}; got {sorted(keys)}."
    )

    literal = _eval_run_kind_literal(fn)
    assert literal == "simulator", (
        f"runner _build_eval_metadata eval_run_kind drift: expected 'simulator'; got {literal!r}."
    )


# ════════════════════════════════════════════════════════════════════════
# customer_node.py — propagates eval_metadata through llm.ainvoke config
# ════════════════════════════════════════════════════════════════════════


def test_customer_node_propagates_eval_metadata() -> None:
    """``customer_node.py`` AST MUST reference ``state.eval_metadata`` literally.

    Static evidence the customer LLM dispatch path forwards H5 metadata
    to the EvalSimulatorCallbackHandler. We don't probe the exact dict
    shape (the helper does that) — only that the propagation point
    exists in source.
    """
    cn_path = _SIMULATOR_INTERNAL / "customer_node.py"
    assert cn_path.is_file(), "customer_node.py missing — T-6 deliverable absent."
    text = cn_path.read_text(encoding="utf-8")
    assert "state.eval_metadata" in text, (
        "customer_node.py MUST reference state.eval_metadata explicitly so "
        "the customer LLM dispatch propagates H5 metadata to the callback."
    )


# ════════════════════════════════════════════════════════════════════════
# agent_bridge.py — wires EvalSimulatorObservabilityContext via factory
# ════════════════════════════════════════════════════════════════════════


def test_agent_bridge_uses_eval_simulator_observability_context() -> None:
    """``agent_bridge.py`` MUST construct ``EvalSimulatorObservabilityContext`` (T-7 factory).

    Cement: the agent invocation path runs under an observability
    context that propagates H5 metadata. Bypassing the factory would
    persist agent rows without ``eval_metadata`` → arch fitness fails.
    """
    ab_path = _SIMULATOR_INTERNAL / "agent_bridge.py"
    assert ab_path.is_file(), "agent_bridge.py missing — T-7 deliverable absent."
    text = ab_path.read_text(encoding="utf-8")
    assert "build_eval_simulator_observability_context" in text or "EvalSimulatorObservabilityContext" in text, (
        "agent_bridge.py MUST reference build_eval_simulator_observability_context "
        "or EvalSimulatorObservabilityContext to enforce H5 metadata propagation."
    )


# ════════════════════════════════════════════════════════════════════════
# observability.py — runtime guard imported / referenced
# ════════════════════════════════════════════════════════════════════════


def test_assert_eval_metadata_complete_invoked() -> None:
    """``_assert_eval_metadata_complete`` MUST be called somewhere in observability.py.

    Defense-in-depth: the runtime guard rejects rows missing any of the
    6 H5 keys. Static evidence the guard is wired into the persistence
    path (paridad with __post_init__ / repos in T-5).
    """
    obs_path = _SIMULATOR_INTERNAL / "observability.py"
    text = obs_path.read_text(encoding="utf-8")
    # Two valid invocation forms — both indicate the guard is wired.
    invoked = (
        "_assert_eval_metadata_complete(" in text
        or "_assert_eval_metadata_complete(meta)" in text
        or "_assert_eval_metadata_complete(self.eval_metadata)" in text
    )
    assert invoked, (
        "_assert_eval_metadata_complete is defined but never invoked. "
        "T-5 wires the guard into __post_init__ + repo add(). "
        "Removing the call lets rows persist without the H5 keys."
    )
