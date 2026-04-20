"""Architecture fitness: SectionCatalog ↔ SectionKey alignment, no orphans, no drift.

Mirrors the pattern of ``test_archetype_catalog_completeness.py``. Failing
this gate means the domain model drifted away from the declared catalog —
any new section key MUST ship alongside its metadata record in the same
commit, and removed keys must purge their entries.

Also enforces the enriched metadata contract introduced in the Latam
mass-market rework (Sprint 8):

- Every entry declares the 3 enrichment fields (``help_text_es``,
  ``completion_weight``, ``required_to_publish``).
- Icons are unique across sections — cross-section collision would show
  the same glyph twice in a single surface.
- ``completion_weight`` sits in [0.1, 1.0] — zero-weighted sections
  would disappear from scoring silently.
- Required-to-publish sections MUST have ``completion_weight >= 0.8`` —
  a "critical" section that barely moves the score signals a
  misconfigured weight.

Related:
- `section_catalog.py` — catalog data.
- `test_section_catalog.py` — unit tests on content + scope assignments.
- `.claude/rules/offer-catalogs.md` — SSoT rule for the offer-studio DAG.
"""

from __future__ import annotations

from src.modules.offer.domain.section_catalog import (
    SECTION_CATALOG,
    SectionKey,
    SectionScope,
)


def test_every_section_key_has_a_catalog_entry() -> None:
    missing = [key for key in SectionKey if key not in SECTION_CATALOG]
    assert missing == [], (
        "Every SectionKey must have a SECTION_CATALOG entry. "
        f"Missing: {missing}. "
        "Add a record to section_catalog.py declaring label_es, subtitle_es, "
        "help_text_es, icon_name, scope, completion_weight, required_to_publish."
    )


def test_catalog_has_no_orphan_entries() -> None:
    enum_values = set(SectionKey)
    catalog_values = set(SECTION_CATALOG.keys())
    orphans = catalog_values - enum_values
    assert orphans == set(), f"Catalog has entries for keys that no longer exist in SectionKey enum: {orphans}"


def test_catalog_records_self_reference_their_key() -> None:
    for key, meta in SECTION_CATALOG.items():
        assert meta.key is key, f"Catalog entry for {key} declares key={meta.key}"


def test_every_entry_has_valid_scope() -> None:
    valid_scopes = set(SectionScope)
    for key, meta in SECTION_CATALOG.items():
        assert meta.scope in valid_scopes, f"{key} has invalid scope {meta.scope!r}"


def test_every_entry_has_required_spanish_copy() -> None:
    for key, meta in SECTION_CATALOG.items():
        assert meta.label_es.strip(), f"{key} has empty label_es"
        assert meta.subtitle_es.strip(), f"{key} has empty subtitle_es"
        assert meta.help_text_es.strip(), f"{key} has empty help_text_es"
        assert meta.icon_name.strip(), f"{key} has empty icon_name"


def test_help_text_is_richer_than_subtitle() -> None:
    """``help_text_es`` should add context beyond ``subtitle_es`` — if both
    are the same length range, whoever filled the catalog probably just
    duplicated the subtitle. Hard cap: help must be at least 1.5x longer."""
    for key, meta in SECTION_CATALOG.items():
        assert len(meta.help_text_es) >= int(len(meta.subtitle_es) * 1.5), (
            f"{key}: help_text_es ({len(meta.help_text_es)} chars) should be "
            f"substantially richer than subtitle_es ({len(meta.subtitle_es)} chars). "
            "Extend it with the WHY + HOW of the section."
        )


def test_completion_weight_in_valid_range() -> None:
    for key, meta in SECTION_CATALOG.items():
        assert 0.1 <= meta.completion_weight <= 1.0, (
            f"{key}: completion_weight {meta.completion_weight} outside [0.1, 1.0]. "
            "Zero-weighted sections would disappear from scoring; sub-0.1 weights "
            "are a design smell."
        )


def test_required_sections_have_high_weight() -> None:
    """A section that blocks publishing but barely moves the completion
    score is a misconfigured weight — users would think they are "mostly
    done" while the publish button stays greyed out."""
    for key, meta in SECTION_CATALOG.items():
        if meta.required_to_publish:
            assert meta.completion_weight >= 0.8, (
                f"{key}: required_to_publish=True but completion_weight="
                f"{meta.completion_weight}. Required sections must weigh >= 0.8."
            )


def test_icon_names_are_unique_across_sections() -> None:
    """Cross-section icon collisions would show the same glyph twice in
    a single surface (the dashboard rail, the wizard's section picker).
    Cross-catalog reuse (e.g. a section sharing a glyph with an archetype)
    is allowed — different surfaces, different context."""
    icons_by_key: dict[str, list[SectionKey]] = {}
    for key, meta in SECTION_CATALOG.items():
        icons_by_key.setdefault(meta.icon_name, []).append(key)
    collisions = {icon: keys for icon, keys in icons_by_key.items() if len(keys) > 1}
    assert not collisions, (
        f"Sections share icons: {collisions}. Each section must have a unique "
        "Lucide glyph so the UI doesn't show the same icon twice in the rail."
    )
