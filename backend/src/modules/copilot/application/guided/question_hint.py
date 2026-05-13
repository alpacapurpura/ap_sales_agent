"""Guided question hint helper (Fase 09.C).

Wraps :func:`next_question` and produces a ui_action-ready dict that
``advance_guided_block`` includes alongside the next-block payload.
The hint highlights the highest-priority missing field in the current
block, helping the LLM phrase a focused question instead of dumping
the whole block at once.

Pure function — no DB, no I/O. Caller resolves the entity ``state``
and passes it in.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luana_core_copilot.application.orchestrator.conversational_questioning import (
    next_question,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "build_question_hint",
]


def _humanize(path: str) -> str:
    """Best-effort human label fallback for a dotted path.

    Mirrors the walker default in ``shared.domain.field_contract`` —
    last segment, underscores → spaces, title-cased.
    """
    last = path.rsplit(".", maxsplit=1)[-1]
    return last.replace("_", " ").strip().title()


def build_question_hint(
    module: str,
    state: Mapping[str, Any],
    *,
    section: str | None = None,
) -> dict[str, Any] | None:
    """Return a ui_action-ready hint dict, or ``None`` if no field to ask.

    Shape::

        {
            "path": "identity.brand_name",
            "section": "identity",
            "question_es": "¿Cómo se llama tu marca?",
            "expects": "una frase corta",   # only when contract.expects is set
        }

    Spanish text precedence: ``human_question_es`` → ``label_es`` →
    humanized path. Caller may further reformulate via LLM if it wants
    extra naturalness — the hint is the seed.
    """
    contract = next_question(module, state, section=section)
    if contract is None:
        return None

    question_es = contract.human_question_es or contract.label_es or _humanize(contract.path)

    payload: dict[str, Any] = {
        "path": contract.path,
        "section": contract.section,
        "question_es": question_es,
    }
    if contract.expects:
        payload["expects"] = contract.expects
    return payload
