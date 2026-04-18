"""Architecture fitness: SectionCatalog ↔ SectionKey alignment, no orphans, no drift.

Mirrors the pattern of ``test_archetype_catalog_completeness.py``. Failing
this gate means the domain model drifted away from the declared catalog —
any new section key MUST ship alongside its metadata record in the same
commit, and removed keys must purge their entries.

Related:
- `section_catalog.py` — catalog data.
- `test_section_catalog.py` — unit tests on content + scope assignments.
- `SPRINT-6-PLAN.md` §Phase A.2 — the arch test that enforces this.
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
        "icon_name, and scope."
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
        assert meta.icon_name.strip(), f"{key} has empty icon_name"
