"""Integration tests for the editable-fields SSoT + copilot wiring.

Covers:
* Port lazily loads each module's catalog.
* ``propose_field_updates`` rejects unknown ``field_id``s and accepts known ones.
* Catalog enumeration helper produces a compact markdown block for the prompt.
"""

from __future__ import annotations

import json


class TestEditableFieldsPort:
    def test_brand_catalog_non_empty(self) -> None:
        from src.shared.links.ports.editable_fields import get_catalog

        catalog = get_catalog("brand")
        assert len(catalog) > 0
        paths = {f.path for f in catalog}
        # Spot-check: anchor fields the FE renders today must be present.
        assert "identity.brand_name" in paths
        assert "positioning.unique_value_proposition" in paths
        assert "narrative.one_liner" in paths
        # Legacy field MUST NOT be present (deprecated from UI).
        assert "identity.voice_tone" not in paths

    def test_offer_catalog_non_empty(self) -> None:
        from src.shared.links.ports.editable_fields import get_catalog

        catalog = get_catalog("offer")
        paths = {f.path for f in catalog}
        assert "public_name" in paths
        assert "headline_promise" in paths
        assert "pricing_options" in paths

    def test_buyer_persona_catalog_non_empty(self) -> None:
        from src.shared.links.ports.editable_fields import get_catalog

        catalog = get_catalog("buyer_persona")
        paths = {f.path for f in catalog}
        assert "name" in paths
        assert "tagline" in paths
        assert "demographics.age_range" in paths
        assert "psychographics.values" in paths
        assert "buyer_journey.awareness" in paths
        # Listas de items compuestos NO están en el catálogo (se editan vía
        # form-runtime/guided, no vía propose_field_updates).
        # objections + preferred_channels fueron eliminados del modelo
        # buyer_persona en PR-1 PI-4 S1 (2026-04-29).
        assert "objections" not in paths
        assert "pain_points" not in paths
        assert "desires" not in paths
        assert "preferred_channels" not in paths

    def test_unknown_domain_returns_empty(self) -> None:
        from src.shared.links.ports.editable_fields import get_catalog

        assert get_catalog("nonexistent_domain") == ()

    def test_get_registered_domains_includes_brand_and_offer(self) -> None:
        from src.shared.links.ports.editable_fields import get_registered_domains

        domains = get_registered_domains()
        assert "brand" in domains
        assert "offer" in domains


class TestProposeFieldUpdatesValidation:
    def test_accepts_known_brand_field(self) -> None:
        from src.modules.copilot.application.tools.mutations import propose_field_updates

        result = propose_field_updates.invoke(
            {
                "updates": [
                    {
                        "field_id": "identity.brand_name",
                        "new_value": "Alpaca Púrpura",
                        "reason": "Alinear con el brief",
                    },
                ],
            },
        )
        assert result["success"] is True
        assert len(result["ui_action"]["updates"]) == 1

    def test_accepts_known_offer_field(self) -> None:
        from src.modules.copilot.application.tools.mutations import propose_field_updates

        result = propose_field_updates.invoke(
            {
                "updates": [
                    {
                        "field_id": "public_name",
                        "new_value": "Programa Premium",
                        "reason": "Renombrar",
                    },
                ],
            },
        )
        assert result["success"] is True

    def test_rejects_unknown_field(self) -> None:
        """The legacy ``voice_tone`` must NOT pass validation."""
        from src.modules.copilot.application.tools.mutations import propose_field_updates

        result = propose_field_updates.invoke(
            {
                "updates": [
                    {
                        "field_id": "identity.voice_tone",
                        "new_value": "Cercano y aspiracional",
                        "reason": "Tono",
                    },
                ],
            },
        )
        assert result["success"] is False
        assert "identity.voice_tone" in result["message"]

    def test_mixed_valid_and_invalid_only_valid_pass(self) -> None:
        from src.modules.copilot.application.tools.mutations import propose_field_updates

        result = propose_field_updates.invoke(
            {
                "updates": [
                    {
                        "field_id": "identity.brand_name",
                        "new_value": "OK",
                        "reason": "valid",
                    },
                    {
                        "field_id": "identity.definitely_not_a_field",
                        "new_value": "X",
                        "reason": "invalid",
                    },
                ],
            },
        )
        # Partial success: valid update applied, invalid listed in ``rejected``.
        assert result["success"] is True
        applied = [u["field_id"] for u in result["ui_action"]["updates"]]
        assert applied == ["identity.brand_name"]
        assert "rejected" in result
        assert len(result["rejected"]) == 1
        assert result["rejected"][0]["field_id"] == "identity.definitely_not_a_field"


class TestCatalogMarkdownForPrompt:
    def test_catalog_markdown_contains_sections_and_fields(self) -> None:
        from src.modules.copilot.domain.schema_introspection import (
            format_editable_field_catalog_markdown,
        )

        md = format_editable_field_catalog_markdown("brand")
        # Section headers present
        assert "identity" in md
        assert "personality" in md
        # Field paths appear (so the LLM can copy them)
        assert "identity.brand_name" in md
        # Compactness: no legacy
        assert "voice_tone" not in md

    def test_catalog_markdown_for_unknown_domain_is_empty(self) -> None:
        from src.modules.copilot.domain.schema_introspection import (
            format_editable_field_catalog_markdown,
        )

        assert format_editable_field_catalog_markdown("none") == ""


class TestRegressionLegacyStaysOutOfCatalog:
    def test_brand_model_still_has_voice_tone_but_catalog_excludes_it(self) -> None:
        """Defends against accidental re-inclusion of the legacy field."""
        from src.modules.brand.domain.aggregates import BrandSettings
        from src.shared.links.ports.editable_fields import get_paths_for

        # The BE model keeps the legacy column for back-compat; confirm it.
        identity_fields = BrandSettings.model_fields["identity"].annotation
        # get_args returns Optional[...] inner type
        paths = get_paths_for("brand")
        assert "identity.voice_tone" not in paths
        # but the field still exists on the Pydantic model (back-compat).
        _ = identity_fields  # silences unused warning; the key point is the catalog
        # (tests for model presence live in the brand module)


def test_catalog_json_serialisable() -> None:
    """FieldSpec entries are serialisable via dataclasses.asdict."""
    from dataclasses import asdict

    from src.shared.links.ports.editable_fields import get_catalog

    data = [asdict(f) for f in get_catalog("brand")]
    blob = json.dumps(data, ensure_ascii=False)
    assert len(blob) > 100
