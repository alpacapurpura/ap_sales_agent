"""Unit tests for the OfferFormat catalog.

A format is a descriptive "flavor" within an archetype (e.g. "Bootcamp" is
a format inside PROGRAMA). Each entry declares:

- Which archetype it belongs to.
- Suitability per ``ExpertBusinessType`` as a 0.0..1.0 score — the wizard
  uses these scores to filter + rank the cards shown to the tenant based
  on ``BrandIdentity.business_types``.
- A stable ``format_hint`` string (the one persisted on offers).
- Its ``delivery_model`` as an informative default (per D2 — not gating).

``suggested_value_level`` is intentionally absent: the ladder rung is a
separate decision the user makes in the wizard.
"""

from __future__ import annotations

import math

from luana_core_offer_studio.domain.enums import OfferArchetype, OfferDeliveryModel
from luana_core_offer_studio.domain.format_catalog import (
    FORMAT_CATALOG,
    FormatMetadata,
    format_ids_for_archetype,
    get_format_metadata,
    get_formats_suitable_for,
)
from luana_core_platform.domain.expert_business_type import ExpertBusinessType


class TestFormatCatalogStructure:
    def test_catalog_is_non_empty(self) -> None:
        assert len(FORMAT_CATALOG) > 0

    def test_every_archetype_has_a_custom_fallback(self) -> None:
        """Each archetype must expose a ``*_custom`` format as escape hatch."""
        for archetype in OfferArchetype:
            ids = format_ids_for_archetype(archetype)
            custom_ids = [i for i in ids if i.endswith("_custom")]
            assert custom_ids, f"archetype {archetype} lacks a _custom fallback format"

    def test_format_ids_are_globally_unique(self) -> None:
        ids = list(FORMAT_CATALOG.keys())
        assert len(ids) == len(set(ids))

    def test_every_format_references_a_valid_archetype(self) -> None:
        valid = set(OfferArchetype)
        for format_id, meta in FORMAT_CATALOG.items():
            assert meta.archetype in valid, f"{format_id} has unknown archetype {meta.archetype}"

    def test_every_format_has_required_localized_fields(self) -> None:
        for format_id, meta in FORMAT_CATALOG.items():
            assert isinstance(meta, FormatMetadata)
            assert meta.format_id == format_id
            assert meta.label_es.strip()
            assert meta.description_es.strip()
            assert meta.icon_name.strip()
            assert meta.format_hint is not None  # "" is allowed for custom

    def test_delivery_model_is_valid(self) -> None:
        valid = set(OfferDeliveryModel)
        for meta in FORMAT_CATALOG.values():
            assert meta.delivery_model in valid


class TestFormatSuitabilityScores:
    def test_suitability_keys_are_valid_business_types(self) -> None:
        valid = set(ExpertBusinessType)
        for format_id, meta in FORMAT_CATALOG.items():
            for business_type in meta.suitable_for:
                assert business_type in valid, f"{format_id} references unknown {business_type}"

    def test_scores_are_in_unit_interval(self) -> None:
        for format_id, meta in FORMAT_CATALOG.items():
            for business_type, score in meta.suitable_for.items():
                assert 0.0 <= score <= 1.0, f"{format_id} suitable_for[{business_type}] = {score} is out of [0.0, 1.0]"
                assert not math.isnan(score)

    def test_every_format_suits_at_least_one_business_type(self) -> None:
        """A format with all zero scores would be unreachable — disallow."""
        for format_id, meta in FORMAT_CATALOG.items():
            positive = [s for s in meta.suitable_for.values() if s > 0]
            assert positive, f"{format_id} is unreachable — no positive suitability scores"

    def test_custom_formats_suit_every_business_type(self) -> None:
        """``_custom`` is the explicit "my format isn't here" escape hatch —
        every business type must be able to see it."""
        for format_id, meta in FORMAT_CATALOG.items():
            if not format_id.endswith("_custom"):
                continue
            for business_type in ExpertBusinessType:
                score = meta.suitable_for.get(business_type, 0.0)
                assert score > 0, f"{format_id} hides from {business_type} — custom must always show"


class TestFormatHelpers:
    def test_format_ids_for_archetype_filters_correctly(self) -> None:
        for archetype in OfferArchetype:
            ids = format_ids_for_archetype(archetype)
            assert all(FORMAT_CATALOG[i].archetype is archetype for i in ids)

    def test_get_format_metadata_returns_frozen_record(self) -> None:
        sample_id = next(iter(FORMAT_CATALOG))
        record = get_format_metadata(sample_id)
        assert record.format_id == sample_id

    def test_get_formats_suitable_for_returns_only_positive_scores(self) -> None:
        """When asking what fits a SaaS founder, results must all have score > 0
        for SOFTWARE_SAAS."""
        results = get_formats_suitable_for(
            business_types=[ExpertBusinessType.SOFTWARE_SAAS],
        )
        assert results, "SaaS founder should see at least the _custom escape hatch"
        for meta in results:
            best = max(meta.suitable_for.get(bt, 0.0) for bt in [ExpertBusinessType.SOFTWARE_SAAS])
            assert best > 0

    def test_get_formats_suitable_for_ranks_by_best_score(self) -> None:
        """With multiple business types, the best score per format wins — and
        results are sorted by descending best score."""
        results = get_formats_suitable_for(
            business_types=[
                ExpertBusinessType.COACH_MENTOR,
                ExpertBusinessType.ACADEMIA_INFOPRODUCTOR,
            ],
        )
        scores = [
            max(
                meta.suitable_for.get(ExpertBusinessType.COACH_MENTOR, 0.0),
                meta.suitable_for.get(ExpertBusinessType.ACADEMIA_INFOPRODUCTOR, 0.0),
            )
            for meta in results
        ]
        assert scores == sorted(scores, reverse=True), "results must be sorted by descending score"

    def test_get_formats_suitable_for_empty_types_returns_all(self) -> None:
        """Empty business_types = onboarding not yet complete. Show everything."""
        results = get_formats_suitable_for(business_types=[])
        assert len(results) == len(FORMAT_CATALOG)

    def test_get_formats_suitable_for_respects_archetype_filter(self) -> None:
        results = get_formats_suitable_for(
            business_types=[ExpertBusinessType.COACH_MENTOR],
            archetype=OfferArchetype.PROGRAMA,
        )
        assert results
        for meta in results:
            assert meta.archetype is OfferArchetype.PROGRAMA
