"""Architectural fitness — editable-fields SSoT integrity.

Ensures the copilot's editable-field contract stays healthy:

* Every registered domain has a non-empty catalog.
* No path is duplicated across domains (prevents ambiguity in the
  ``propose_field_updates`` guess_domain logic).
* Known-legacy fields that have been removed from the UI MUST NOT
  reappear in the catalog (ratchet-style guard).

A failing test here usually means someone renamed/added/removed a form
schema in the frontend without updating the matching catalog file.
"""

from __future__ import annotations

import pytest

from src.shared.links.ports.editable_fields import (
    get_catalog,
    get_paths_for,
    get_registered_domains,
)

# Fields that the FE no longer renders. They may still exist on the
# Pydantic model for back-compat, but must NOT be proposed by the copilot.
_DEPRECATED_PATHS: frozenset[str] = frozenset(
    {
        "identity.voice_tone",
    },
)


class TestCatalogsRegistered:
    def test_brand_catalog_registered(self) -> None:
        assert len(get_catalog("brand")) > 0

    def test_offer_catalog_registered(self) -> None:
        assert len(get_catalog("offer")) > 0

    def test_known_domains_reported(self) -> None:
        domains = get_registered_domains()
        assert "brand" in domains
        assert "offer" in domains


class TestCatalogIntegrity:
    def test_no_duplicate_paths_within_domain(self) -> None:
        for domain in get_registered_domains():
            catalog = get_catalog(domain)
            paths = [f.path for f in catalog]
            assert len(paths) == len(set(paths)), (
                f"Domain '{domain}' has duplicate paths: {[p for p in paths if paths.count(p) > 1]}"
            )

    def test_no_cross_domain_duplicates(self) -> None:
        seen: dict[str, str] = {}
        for domain in get_registered_domains():
            for spec in get_catalog(domain):
                if spec.path in seen:
                    pytest.fail(
                        f"Path '{spec.path}' duplicated in '{domain}' and '{seen[spec.path]}'",
                    )
                seen[spec.path] = domain

    def test_no_legacy_paths_in_any_catalog(self) -> None:
        for domain in get_registered_domains():
            paths = get_paths_for(domain)
            offenders = _DEPRECATED_PATHS & paths
            assert not offenders, (
                f"Deprecated paths reappeared in domain '{domain}': {offenders}. "
                "These fields were removed from the UI — remove them from the "
                "catalog file too."
            )


class TestFieldSpecShape:
    def test_every_field_has_path_label_section(self) -> None:
        for domain in get_registered_domains():
            for spec in get_catalog(domain):
                assert spec.path, f"empty path in {domain}"
                assert spec.label, f"empty label for {spec.path} in {domain}"
                assert spec.section, f"empty section for {spec.path} in {domain}"
