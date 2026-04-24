"""Tests for offer worker section grouping (Bug 1 regression).

Verifies that after the fix the worker uses FE section slugs in the
filled_fields_by_section Redis payload — NOT flat top-level field names
or backend wave slugs.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.extraction_section_map import (
    fields_to_fe_sections,
)


class TestFieldsToFeSectionsIntegration:
    """Integration-level checks: the grouping function produces FE slugs, not flat keys."""

    def test_flat_field_name_is_not_used_as_slug(self) -> None:
        """headline_promise must NOT appear as a section key — it must land under 'identity'."""
        result = fields_to_fe_sections(
            archetype=OfferArchetype.PROGRAMA,
            filled_paths=["headline_promise", "value_level"],
        )
        assert "headline_promise" not in result, (
            "Bug 1 regression: flat field name 'headline_promise' appears as a section key. Must land under 'identity'."
        )
        assert "identity" in result

    def test_value_level_not_a_section_key(self) -> None:
        """value_level must NOT appear as a section key — it must land under 'strategy'."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["value_level"],
        )
        assert "value_level" not in result
        assert "strategy" in result

    def test_deliverables_not_a_section_key(self) -> None:
        """deliverables must NOT appear as a section key — it must land under 'value_stack'."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["deliverables"],
        )
        assert "deliverables" not in result
        assert "value_stack" in result

    def test_guarantee_type_not_a_section_key(self) -> None:
        """guarantee_type must NOT appear as a section key — it must land under 'closing'."""
        result = fields_to_fe_sections(
            archetype=None,
            filled_paths=["guarantee_type"],
        )
        assert "guarantee_type" not in result
        assert "closing" in result

    def test_all_output_keys_are_fe_slugs(self) -> None:
        """All keys in the result must be valid FE section slugs."""
        from src.modules.offer.domain.extraction_section_map import FE_SECTION_SLUGS

        paths = [
            "headline_promise",
            "value_level",
            "deliverables",
            "guarantee_type",
            "instructors",
            "pricing_options",
            "marketing_pain_points",
            "specific_details.duration_weeks",
        ]
        result = fields_to_fe_sections(
            archetype=OfferArchetype.PROGRAMA,
            filled_paths=paths,
        )
        for key in result:
            assert key in FE_SECTION_SLUGS, (
                f"Key '{key}' in fields_to_fe_sections output is not a valid FE section slug. "
                "This would cause the UI to show a badge for a non-existent section."
            )


class TestOfferExtractionRoutes:
    """Tests for offer/application/extraction_routes.py."""

    def test_nav_route_template_format(self) -> None:
        """NAV_ROUTE_TEMPLATE includes all required placeholders."""
        from src.modules.offer.application.extraction_routes import NAV_ROUTE_TEMPLATE

        assert "{tenantId}" in NAV_ROUTE_TEMPLATE
        assert "{entityId}" in NAV_ROUTE_TEMPLATE
        assert "{section_slug}" in NAV_ROUTE_TEMPLATE

    def test_primary_cta_route_includes_offer_id(self) -> None:
        """primary_cta_route includes the offer_id in the path."""
        from src.modules.offer.application.extraction_routes import primary_cta_route

        offer_id = str(uuid.uuid4())
        route = primary_cta_route(offer_id, ["identity", "strategy"])
        assert offer_id in route
        assert "identity" in route  # first section
        assert "{tenantId}" in route  # literal placeholder for FE

    def test_primary_cta_route_none_when_no_sections(self) -> None:
        """primary_cta_route returns None when sections_completed is empty."""
        from src.modules.offer.application.extraction_routes import primary_cta_route

        assert primary_cta_route("some-id", []) is None

    def test_primary_cta_route_not_brand_studio(self) -> None:
        """primary_cta_route must NOT contain 'brand-studio' (Bug 2 regression)."""
        from src.modules.offer.application.extraction_routes import primary_cta_route

        offer_id = str(uuid.uuid4())
        route = primary_cta_route(offer_id, ["identity"])
        assert "brand-studio" not in route, (
            "Bug 2 regression: offer primary_cta_route points to brand-studio. Must point to offer-studio editor."
        )


class TestBrandExtractionRoutes:
    """Tests for brand/application/extraction_routes.py."""

    def test_nav_route_template_brand_format(self) -> None:
        """Brand NAV_ROUTE_TEMPLATE uses brand-studio pattern."""
        from src.modules.brand.application.extraction_routes import NAV_ROUTE_TEMPLATE

        assert "{tenantId}" in NAV_ROUTE_TEMPLATE
        assert "{section_slug}" in NAV_ROUTE_TEMPLATE
        assert "brand-studio" in NAV_ROUTE_TEMPLATE

    def test_brand_primary_cta_route_no_entity_id(self) -> None:
        """Brand primary_cta_route does NOT include {entityId} (brand has no entity ID)."""
        from src.modules.brand.application.extraction_routes import primary_cta_route

        route = primary_cta_route(["identity"])
        assert "{entityId}" not in route
        assert "identity" in route

    def test_brand_primary_cta_route_none_when_empty(self) -> None:
        """Brand primary_cta_route returns None for empty sections."""
        from src.modules.brand.application.extraction_routes import primary_cta_route

        assert primary_cta_route([]) is None
