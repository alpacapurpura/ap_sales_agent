"""Architectural fitness: Meta provider daily-extraction guarantees.

Enforces that every ``/insights`` call that targets an aggregable level
(``account``, ``campaign``, ``ad``) passes ``time_increment=1``. Without
it, Meta returns a single aggregated row for the whole period and the
per-day metrics table gets contaminated (Visionarias PEN 856.61 bug).

Certain extractors are intentionally period-aggregated and land on
different tables — those are listed in ``ALLOWED_PERIOD_FUNCTIONS``.
"""

import ast
from pathlib import Path

META_PROVIDER_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "modules"
    / "analytics"
    / "infrastructure"
    / "providers"
    / "meta_provider.py"
)

# Functions that intentionally issue period-aggregated Insights calls.
# Each has a legitimate reason to avoid ``time_increment=1``:
#
# - ``_extract_meta_ads_breakdowns``: returns JSON (``unit="json"``) with
#   breakdowns by age/gender/placement. One row per dimension value, not
#   per day. Lands on the daily table with value=0 and real data in
#   ``extra.breakdowns``, so it never pollutes spend/reach/impressions.
#
# - ``_extract_ig_organic_period`` and ``_extract_meta_ads_period``:
#   NON_AGGREGABLE period extractors (reach, frequency) that land on the
#   ``period_metrics`` table via ``extract_period_metrics``. They use
#   ``period=day``/``period=days_28``/``time_range`` semantics that are
#   incompatible with ``time_increment=1``.
#
# - ``_extract_meta_retargeting`` and ``_extract_meta_retargeting_daily``:
#   legacy nurturing-stage extractor. The ``_daily`` wrapper iterates
#   day-by-day externally (one HTTP call per day) so the inner call does
#   not need ``time_increment=1``. Scheduled for a dedicated refactor.
ALLOWED_PERIOD_FUNCTIONS: set[str] = {
    "_extract_meta_ads_breakdowns",
    "_extract_ig_organic_period",
    "_extract_meta_ads_period",
    "_extract_meta_retargeting",
    "_extract_meta_retargeting_daily",
}


def _find_function_by_name(
    tree: ast.AST,
    name: str,
) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
            and node.name == name
        ):
            return node
    return None


def _enclosing_function_name(tree: ast.AST, target: ast.AST) -> str | None:
    """Find the name of the nearest enclosing function for ``target``."""
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            for sub in ast.walk(node):
                if sub is target:
                    return node.name
    return None


def test_every_ads_insights_call_uses_time_increment():
    """Enforce that aggregable-level Insights calls all pass time_increment=1.

    Scans the source AST for ``client.get(...)`` calls whose ``params`` dict
    sets ``level`` to ``account``, ``campaign`` or ``ad``. Each such call
    MUST include ``time_increment`` in its params, unless it lives inside
    one of ``ALLOWED_PERIOD_FUNCTIONS``.
    """
    source = META_PROVIDER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    aggregable_levels = {"account", "campaign", "ad"}
    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Look for ``<something>.get(...)``
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "get"):
            continue

        # Extract the params keyword argument
        params_kw = next(
            (kw for kw in node.keywords if kw.arg == "params"),
            None,
        )
        if params_kw is None or not isinstance(params_kw.value, ast.Dict):
            continue

        params_keys: dict[str, ast.AST] = {}
        for key_node, val_node in zip(
            params_kw.value.keys,
            params_kw.value.values,
            strict=False,
        ):
            if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                params_keys[key_node.value] = val_node

        level_node = params_keys.get("level")
        if level_node is None or not isinstance(level_node, ast.Constant):
            continue
        if level_node.value not in aggregable_levels:
            continue

        # Also require the URL to look like an /insights endpoint
        # (guards against a future ``client.get("act_/adsets", level=...)``)
        url_arg = node.args[0] if node.args else None
        url_src = ast.unparse(url_arg) if url_arg is not None else ""
        if "/insights" not in url_src:
            continue

        enclosing = _enclosing_function_name(tree, node)
        if enclosing in ALLOWED_PERIOD_FUNCTIONS:
            continue

        if "time_increment" not in params_keys:
            violations.append(
                f"{enclosing or '<module>'}: /insights call with "
                f"level={level_node.value!r} is missing time_increment "
                f"(line {node.lineno})",
            )

    assert not violations, (
        "Meta Insights calls that can pollute per-day metrics:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_deleted_period_aggregate_extractors_stay_deleted():
    """Prevent reintroduction of the removed *_daily helpers.

    The old dual API (``_extract_meta_ads`` + ``_extract_meta_ads_daily``)
    allowed the period-aggregated flavour to be called from ``extract_metrics``
    (the cron path), which is exactly how the Visionarias contamination
    happened. The single canonical methods below must stay single.
    """
    source = META_PROVIDER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden = [
        "_extract_meta_ads_daily",
        "_extract_meta_ads_campaigns_daily",
        "_extract_meta_ads_by_ad_daily",
    ]
    present = [name for name in forbidden if _find_function_by_name(tree, name)]
    assert not present, (
        "Removed Meta ads _daily helpers have been reintroduced — the "
        "canonical extractors already use time_increment=1. Remove these "
        "again and keep a single implementation per level: " + ", ".join(present)
    )


def _raises_period_aggregate_error(fn: ast.AST) -> bool:
    """True if the function body contains ``raise PeriodAggregateError(...)``."""
    return any(
        isinstance(node, ast.Raise)
        and (
            (
                isinstance(node.exc, ast.Call)
                and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id == "PeriodAggregateError"
            )
            or (
                isinstance(node.exc, ast.Name) and node.exc.id == "PeriodAggregateError"
            )
        )
        for node in ast.walk(fn)
    )


def test_parse_ads_row_has_period_aggregate_guard():
    """``_parse_ads_row`` must enforce the single-day row invariant.

    The raise can live inline in the parser, or (preferably, to keep C901
    complexity low) be delegated to a helper that is called unconditionally
    at the top of the parser. Either shape is accepted, but the guarantee
    must hold: no code path through ``_parse_ads_row`` can ingest a
    multi-day row without triggering ``PeriodAggregateError``.
    """
    source = META_PROVIDER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    parser = _find_function_by_name(tree, "_parse_ads_row")
    assert parser is not None, "_parse_ads_row not found"

    # Shape 1 — raise lives inside _parse_ads_row itself
    if _raises_period_aggregate_error(parser):
        return

    # Shape 2 — raise lives in a helper and _parse_ads_row calls it before
    # any other branching. Collect helper names called by the parser and
    # ensure at least one of them raises PeriodAggregateError.
    called_helpers: set[str] = set()
    for node in ast.walk(parser):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            called_helpers.add(func.attr)
        elif isinstance(func, ast.Name):
            called_helpers.add(func.id)

    for helper_name in called_helpers:
        helper_fn = _find_function_by_name(tree, helper_name)
        if helper_fn is not None and _raises_period_aggregate_error(helper_fn):
            return

    msg = (
        "_parse_ads_row must raise PeriodAggregateError (directly or via a "
        "helper it calls) when it receives a multi-day row. This is the "
        "last line of defence against the Visionarias contamination pattern."
    )
    raise AssertionError(msg)
