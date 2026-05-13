"""Architecture fitness: FORMAT_CATALOG consistency with its enum inputs.

The format catalog is a domain invariant: adding a new archetype, removing
a business type, or letting a suitability score drift outside [0, 1] must
fail CI. All invariants that matter for correctness (format_id unique,
archetype valid, keys are valid ExpertBusinessType, scores in range) live
in the unit test. This file keeps the top-level contract the archetype
catalog already has: every archetype must have at least one entry.
"""

from __future__ import annotations

from luana_core_offer_studio.domain.enums import OfferArchetype
from luana_core_offer_studio.domain.format_catalog import FORMAT_CATALOG


def test_every_archetype_has_at_least_one_format() -> None:
    covered = {meta.archetype for meta in FORMAT_CATALOG.values()}
    missing = set(OfferArchetype) - covered
    assert missing == set(), (
        f"Every OfferArchetype must have at least one format in FORMAT_CATALOG. Missing coverage: {missing}."
    )


def test_format_ids_follow_archetype_prefix_convention() -> None:
    """Stable IDs make the persisted ``format_hint`` traceable — enforce
    ``{archetype}_{slug}`` prefix so joins to analytics are possible."""
    for format_id, meta in FORMAT_CATALOG.items():
        expected_prefix = f"{meta.archetype.value}_"
        assert format_id.startswith(expected_prefix), (
            f"format_id {format_id!r} must start with {expected_prefix!r} "
            "(archetype enum value) so it remains traceable."
        )
