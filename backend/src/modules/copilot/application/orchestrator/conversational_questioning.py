"""Channel-agnostic conversational questioning algorithm (Fase 09).

Selects the next ``FieldContract`` to ask the user about, given the
current data state for a module. Pure function — no I/O, no LLM, no
DB. Caller (web copilot guided advance, future chat adapter, future
voice / email adapter) decides how to render the contract returned.

Selection rules — see ``DESIGN.md`` §2.5 + ``SPEC.md`` Fase 09:

- ``status == FieldStatus.ACTIVE`` (deprecated / removed never offered).
- ``can_propose == True`` (read-only fields skipped).
- value at ``contract.path`` is missing (None / ""/ blank / [] / {}).
  Booleans ``False`` and numeric ``0`` are NOT missing.
- ``gate`` (precondition path) satisfied — None gate or
  state[gate] non-empty.

Ordering — first match wins:

- Required-missing (``is_required_semantic=True``) before optional-missing.
- Within the same required-tier: ``(section, -priority, path)``.

Section filter (``section: str | None``) restricts candidates to the
given section. Useful for "advance within current block".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.shared.domain.field_contract import (
    FieldStatus,
    get_module_contracts,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.shared.domain.field_contract import FieldContract


__all__ = [
    "next_question",
]


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _is_missing(value: Any) -> bool:  # noqa: ANN401 — accepts any state value
    """Return True when ``value`` counts as "not provided" for questioning.

    Missing: ``None``, blank string, empty list / tuple / set / dict.
    Not missing: any non-empty container, any non-blank string, any
    number (including 0), any boolean (including False).
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _get_path(state: Mapping[str, Any], path: str) -> Any:  # noqa: ANN401 — returns any state value
    """Resolve dotted ``path`` against ``state``, returning ``None`` if missing.

    Stops descending if it hits a non-dict before reaching the final
    segment (returns ``None`` rather than raising).
    """
    cursor: Any = state
    for segment in path.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(segment)
        if cursor is None:
            return None
    return cursor


def _gate_satisfied(gate: str | None, state: Mapping[str, Any]) -> bool:
    """Return True when ``gate`` is None or the gated path holds a value."""
    if gate is None:
        return True
    return not _is_missing(_get_path(state, gate))


# --------------------------------------------------------------------------- #
# next_question                                                               #
# --------------------------------------------------------------------------- #


def next_question(
    module: str,
    state: Mapping[str, Any],
    *,
    section: str | None = None,
) -> FieldContract | None:
    """Pick the next ``FieldContract`` to ask the user about, or ``None``.

    Args:
        module: The owning module name (``"offer"`` / ``"brand"`` /
            ``"buyer_persona"`` / …). When unknown returns ``None``.
        state: Current data snapshot for the module. Dotted-path
            resolution applies (``state["a"]["b"]`` for path ``"a.b"``).
        section: Optional section filter — restricts candidates to
            contracts whose ``section`` matches.

    Returns:
        The next contract by selection rules, or ``None`` if there are
        no eligible candidates.

    The returned contract is the registry's frozen instance — callers
    must not mutate it. Use ``contract.human_question_es`` (with
    fallback to ``label_es`` / humanized path) for user-facing text.
    """
    contracts = get_module_contracts(module)
    if not contracts:
        return None

    required: list[FieldContract] = []
    optional: list[FieldContract] = []

    for c in contracts:
        if c.status != FieldStatus.ACTIVE:
            continue
        if not c.can_propose:
            continue
        if section is not None and c.section != section:
            continue
        if not _is_missing(_get_path(state, c.path)):
            continue
        if not _gate_satisfied(c.gate, state):
            continue
        if c.is_required_semantic:
            required.append(c)
        else:
            optional.append(c)

    pool = required or optional
    if not pool:
        return None

    pool.sort(key=lambda c: (c.section, -c.priority, c.path))
    return pool[0]
