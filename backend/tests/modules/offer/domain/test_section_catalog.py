"""Tests for the SectionCatalog (single source of truth for offer-studio sections).

Guards the domain-level contract that every section key has a well-defined
metadata record, that section scopes fall into the allowed set, and that the
lookup helpers behave correctly.

Related:
- `section_catalog.py` — canonical data.
- `test_section_catalog_completeness.py` — architecture fitness test
  (enum ↔ catalog alignment, cross-catalog constraints).
- `SPRINT-6-PLAN.md` §Phase A.1 — the decision locking this as SSoT axis #5.
"""

from __future__ import annotations

import pytest

from src.modules.offer.domain.section_catalog import (
    SECTION_CATALOG,
    SectionKey,
    SectionMetadata,
    SectionScope,
    get_section,
)


class TestCatalogCompleteness:
    def test_every_section_key_has_a_metadata_record(self) -> None:
        missing = [key for key in SectionKey if key not in SECTION_CATALOG]
        assert missing == [], f"Missing catalog entries: {missing}"

    def test_get_section_returns_a_frozen_record(self) -> None:
        meta = get_section(SectionKey.IDENTITY)
        assert isinstance(meta, SectionMetadata)
        with pytest.raises(AttributeError):
            meta.label_es = "mutated"  # type: ignore[misc]

    def test_catalog_records_self_reference_their_key(self) -> None:
        for key, meta in SECTION_CATALOG.items():
            assert meta.key is key, f"Catalog entry for {key} declares key={meta.key}"

    def test_catalog_has_no_orphan_entries(self) -> None:
        enum_values = set(SectionKey)
        catalog_values = set(SECTION_CATALOG.keys())
        orphans = catalog_values - enum_values
        assert orphans == set(), f"Catalog has entries for keys not in the enum: {orphans}"


class TestSectionScope:
    """Scope values are the locked contract D22: OFFER_LEVEL | EDITION_LEVEL | MIXED."""

    def test_every_entry_has_a_valid_scope(self) -> None:
        for key, meta in SECTION_CATALOG.items():
            assert meta.scope in SectionScope, f"{key} has invalid scope {meta.scope}"

    @pytest.mark.parametrize(
        ("section", "expected_scope"),
        [
            # Pure offer-level sections — shared across all editions.
            (SectionKey.IDENTITY, SectionScope.OFFER_LEVEL),
            (SectionKey.STRATEGY, SectionScope.OFFER_LEVEL),
            (SectionKey.PSYCHOLOGY, SectionScope.OFFER_LEVEL),
            (SectionKey.PROMISE, SectionScope.OFFER_LEVEL),
            (SectionKey.VALUE_STACK, SectionScope.OFFER_LEVEL),
            (SectionKey.INSTRUCTORS, SectionScope.OFFER_LEVEL),
            (SectionKey.KNOWLEDGE, SectionScope.OFFER_LEVEL),
            (SectionKey.CLOSING, SectionScope.OFFER_LEVEL),
            (SectionKey.PRODUCT_DETAILS, SectionScope.OFFER_LEVEL),
            (SectionKey.SUBSCRIPTION_DETAILS, SectionScope.OFFER_LEVEL),
            (SectionKey.GALLERY, SectionScope.OFFER_LEVEL),
            # Pure edition-level — requires a LaunchEdition row to edit.
            (SectionKey.EVENT_DETAILS, SectionScope.EDITION_LEVEL),
            # Mixed — per-field owner split.
            (SectionKey.PRICING, SectionScope.MIXED),
            (SectionKey.PROGRAM_DETAILS, SectionScope.MIXED),
            (SectionKey.SERVICE_DETAILS, SectionScope.MIXED),
            (SectionKey.RESOURCES, SectionScope.MIXED),
        ],
    )
    def test_locked_scope_assignments(self, section: SectionKey, expected_scope: SectionScope) -> None:
        """D22 scope assignments — changes here MUST be paired with frontend schema updates."""
        assert SECTION_CATALOG[section].scope is expected_scope


class TestSectionMetadata:
    def test_every_entry_has_non_empty_spanish_labels(self) -> None:
        for key, meta in SECTION_CATALOG.items():
            assert meta.label_es.strip(), f"{key} has empty label_es"
            # subtitle is optional but if set must not be empty-after-strip.
            assert meta.subtitle_es.strip(), f"{key} has empty subtitle_es"

    def test_every_entry_declares_an_icon_name(self) -> None:
        for key, meta in SECTION_CATALOG.items():
            assert meta.icon_name.strip(), f"{key} has empty icon_name"

    def test_icon_names_use_pascalcase_lucide_convention(self) -> None:
        # Lucide icons are PascalCase (e.g. "Target", "RefreshCw"). The frontend
        # resolver maps these strings to components; anything else will be a
        # rendering NOP and surface as a support ticket.
        for key, meta in SECTION_CATALOG.items():
            assert meta.icon_name[0].isupper(), f"{key} icon_name '{meta.icon_name}' must be PascalCase"


class TestGetSection:
    def test_returns_matching_metadata(self) -> None:
        meta = get_section(SectionKey.PRICING)
        assert meta.key is SectionKey.PRICING
        assert meta.scope is SectionScope.MIXED

    def test_raises_on_unknown_key(self) -> None:
        # SectionKey is an StrEnum — direct invalid input would raise at construction.
        # Here we simulate a stale reference by mutating the catalog temporarily.
        sentinel = object()
        with pytest.raises((KeyError, TypeError)):
            get_section(sentinel)  # type: ignore[arg-type]
