"""Offer prompt renderer — Field Contract gating for sales-agent identity.

Bridges :data:`OFFER_FIELD_CONTRACTS` (lifecycle SSoT) and the
:mod:`agent_identity` Jinja template. Today ships the lifecycle gate
only — fields with ``status != ACTIVE`` are stripped from the offer
dict before render — without changing the template syntactically. This
keeps the prompt byte-identical for offers that touch only ACTIVE
fields while making deprecations *automatic*: marking a field
DEPRECATED in the contract is enough to remove it from every tenant's
prompt on the next build, with zero template churn.

Deferred to a future phase (see Fase 05 LEARNINGS):

- Replacing the hardcoded ``{% if offer.X %}`` chain with a
  ``{% for line in offer.prompt_lines %}`` loop driven by
  ``prompt_label_es`` overrides. The current template's whitespace
  handling produces deliberately squashed marker lines that ``trim_blocks``
  strips between ``{% endif %}`` tags; reproducing this byte-identically
  in Python requires per-field renderers + a serialised ``prompt_block``
  string, which is out of scope for the lifecycle-gate sub-step.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

from typing import Any

from src.shared.domain.field_contract import FieldStatus, get_module_contracts


def _inactive_offer_paths() -> frozenset[str]:
    """Top-level offer paths whose contract status disables them.

    Limited to top-level fields because :data:`agent_identity.j2` only
    references ``offer.<top_level>`` paths today; nested
    ``specific_details.*`` and ``platform_details.*`` paths surface via
    other consumers (extraction worker, copilot) which already honour
    contract status independently.
    """
    return frozenset(
        c.path for c in get_module_contracts("offer") if c.status != FieldStatus.ACTIVE and "." not in c.path
    )


def filter_offer_for_prompt(offer_data: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``offer_data`` with inactive contract paths removed.

    Wrapping :func:`build_identity` consumers with this helper makes the
    Jinja template (``{% if offer.X %}``) skip any field that has been
    deprecated or removed in the contract — enabling lifecycle-driven
    deprecations without template edits (ADR-013).

    Enrichment-only keys (``preset_label``, ``preset_description``,
    ``preset_flags``) are preserved untouched: they live outside the
    ``Offer`` model and outside the contract by design.
    """
    inactive = _inactive_offer_paths()
    if not inactive:
        return dict(offer_data)
    return {key: value for key, value in offer_data.items() if key not in inactive}


__all__ = [
    "filter_offer_for_prompt",
]
