"""Architecture fitness: BrandSectionCatalog ↔ BrandSectionKey alignment.

Mirrors the pattern of
``tests/architecture/test_section_catalog_completeness.py`` (offer-studio)
at a smaller scale — brand sections are simpler (no scope, no weight, no
help_text) because per-archetype filtering does not apply.

Related:
- `brand/domain/section_catalog.py` — catalog data.
- `frontend/src/features/brand-studio/lib/section-catalog.ts` — legacy
  FE hardcoded array (scheduled for removal in Fase 03 · Block D).
"""

from __future__ import annotations

from src.modules.brand.domain.section_catalog import (
    BRAND_SECTION_CATALOG,
    BrandSectionKey,
    BrandSectionKind,
)


def test_every_brand_section_key_has_a_catalog_entry() -> None:
    missing = [key for key in BrandSectionKey if key not in BRAND_SECTION_CATALOG]
    assert missing == [], (
        "Every BrandSectionKey must have a BRAND_SECTION_CATALOG entry. "
        f"Missing: {missing}. Add a record declaring label_es, icon_name, kind."
    )


def test_brand_catalog_has_no_orphan_entries() -> None:
    enum_values = set(BrandSectionKey)
    orphans = set(BRAND_SECTION_CATALOG.keys()) - enum_values
    assert orphans == set(), f"Catalog has entries for keys missing from BrandSectionKey enum: {orphans}"


def test_brand_catalog_records_self_reference_their_key() -> None:
    for key, meta in BRAND_SECTION_CATALOG.items():
        assert meta.key is key, f"Catalog entry for {key} declares key={meta.key}"


def test_brand_every_entry_has_required_copy() -> None:
    for key, meta in BRAND_SECTION_CATALOG.items():
        assert meta.label_es.strip(), f"{key} has empty label_es"
        assert meta.icon_name.strip(), f"{key} has empty icon_name"


def test_brand_every_entry_has_valid_kind() -> None:
    valid_kinds = set(BrandSectionKind)
    for key, meta in BRAND_SECTION_CATALOG.items():
        assert meta.kind in valid_kinds, f"{key} has invalid kind {meta.kind!r}"


def test_brand_icon_names_are_unique_across_sections() -> None:
    """Cross-section icon collisions would show the same glyph twice in
    a single surface (the dashboard rail)."""
    icons_by_key: dict[str, list[BrandSectionKey]] = {}
    for key, meta in BRAND_SECTION_CATALOG.items():
        icons_by_key.setdefault(meta.icon_name, []).append(key)
    collisions = {icon: keys for icon, keys in icons_by_key.items() if len(keys) > 1}
    assert not collisions, f"Brand sections share icons: {collisions}. Each section must have a unique Lucide glyph."
