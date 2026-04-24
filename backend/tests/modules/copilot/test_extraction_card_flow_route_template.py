"""Tests for extraction_card_flow route template logic (Bug 2 regression).

Verifies that emit_section_complete_pill uses the nav_route_template from
the event payload rather than generating a hardcoded module-slug route.
Also verifies the summary card no longer falls back to brand-studio.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CONVERSATION_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
JOB_ID = str(uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"))
OFFER_ID = str(uuid.uuid4())


class TestNavPillRouteTemplate:
    """Verify emit_section_complete_pill uses the module-owned route template."""

    def _make_appender(self) -> tuple[list[dict], MagicMock]:
        """Build a mock ConversationRepository that collects appended messages."""
        appended: list[dict] = []
        repo = MagicMock()
        repo.append_messages = MagicMock(side_effect=lambda conv_id, tid, msgs, **kw: appended.extend(msgs))
        return appended, repo

    def test_uses_nav_route_template_for_offer(self) -> None:
        """When nav_route_template is provided, route uses it with section_slug substituted."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )
        from src.modules.offer.application.extraction_routes import NAV_ROUTE_TEMPLATE

        appended, repo_mock = self._make_appender()
        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=repo_mock,
            ),
        ):
            emit_section_complete_pill(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug="identity",
                section_label="Identidad",
                fields_count=3,
                module="offer",
                nav_route_template=NAV_ROUTE_TEMPLATE,
                entity_id=OFFER_ID,
            )

        assert len(appended) == 1
        payload = appended[0]["blocks"][0]["payload"]
        route = payload["route"]

        # Route must contain offer_id (not brand-studio)
        assert OFFER_ID in route, f"offer_id not in route: {route}"
        assert "offer-studio" in route, f"route does not contain 'offer-studio': {route}"
        assert "brand-studio" not in route, f"route incorrectly contains 'brand-studio': {route}"
        # Section slug must be substituted
        assert "identity" in route, f"section_slug 'identity' not in route: {route}"
        # tenantId placeholder must remain for FE to substitute
        assert "{tenantId}" in route, f"tenantId placeholder missing from route: {route}"
        # entityId placeholder must be replaced
        assert "{entityId}" not in route, f"entityId placeholder still in route: {route}"

    def test_legacy_fallback_when_no_template(self) -> None:
        """When nav_route_template is None, falls back to module-slug route (backward compat)."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        appended, repo_mock = self._make_appender()
        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=repo_mock,
            ),
        ):
            emit_section_complete_pill(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug="identity",
                section_label="Identidad",
                fields_count=3,
                module="brand",
                nav_route_template=None,  # Legacy event without template
            )

        assert len(appended) == 1
        payload = appended[0]["blocks"][0]["payload"]
        route = payload["route"]
        # Legacy fallback builds brand-studio route
        assert "brand-studio" in route, f"Legacy fallback route incorrect: {route}"
        assert "{tenantId}" in route

    def test_brand_route_template(self) -> None:
        """Brand nav_route_template produces brand-studio URL without entityId."""
        from src.modules.brand.application.extraction_routes import NAV_ROUTE_TEMPLATE as BRAND_TPL
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        appended, repo_mock = self._make_appender()
        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=repo_mock,
            ),
        ):
            emit_section_complete_pill(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug="strategy",
                section_label="Estrategia",
                fields_count=2,
                module="brand",
                nav_route_template=BRAND_TPL,
                entity_id=None,
            )

        assert len(appended) == 1
        payload = appended[0]["blocks"][0]["payload"]
        route = payload["route"]
        assert "brand-studio" in route
        assert "strategy" in route
        assert "{tenantId}" in route
        assert "{entityId}" not in route  # brand has no entity_id


class TestSummaryCardNoBrandStudioFallback:
    """Verify emit_extraction_summary_card does not hardcode brand-studio as fallback CTA."""

    def _make_appender(self) -> tuple[list[dict], MagicMock]:
        appended: list[dict] = []
        repo = MagicMock()
        repo.append_messages = MagicMock(side_effect=lambda conv_id, tid, msgs, **kw: appended.extend(msgs))
        return appended, repo

    def test_summary_card_with_no_cta_emits_none(self) -> None:
        """When primary_cta_route=None and no fallback, summary has cta=None."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )

        appended, repo_mock = self._make_appender()
        unique_job = str(uuid.uuid4())
        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=repo_mock,
            ),
        ):
            emit_extraction_summary_card(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=unique_job,
                source_ref="https://example.com",
                duration_seconds=10,
                filled_fields=["headline_promise"],
                filled_fields_by_section={"identity": ["headline_promise"]},
                sections_completed=["identity"],
                primary_cta_route=None,
            )

        assert len(appended) == 1
        payload = appended[0]["blocks"][0]["payload"]
        # Must NOT default to brand-studio when primary_cta_route is None
        cta = payload.get("primary_cta_route")
        assert cta is None, (
            f"Bug 2 regression: summary card CTA should be None when no route provided, "
            f"but got: {cta!r}. This causes offer summaries to navigate to brand-studio."
        )

    def test_summary_card_with_offer_cta_not_brand_studio(self) -> None:
        """When primary_cta_route points to offer-studio, it is used as-is."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )
        from src.modules.offer.application.extraction_routes import primary_cta_route

        offer_id = str(uuid.uuid4())
        cta = primary_cta_route(offer_id, ["identity"])

        appended, repo_mock = self._make_appender()
        unique_job = str(uuid.uuid4())
        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=repo_mock,
            ),
        ):
            emit_extraction_summary_card(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=unique_job,
                source_ref="https://offer.com",
                duration_seconds=20,
                filled_fields=["headline_promise"],
                filled_fields_by_section={"identity": ["headline_promise"]},
                sections_completed=["identity"],
                primary_cta_route=cta,
            )

        assert len(appended) == 1
        payload = appended[0]["blocks"][0]["payload"]
        out_cta = payload["primary_cta_route"]
        assert "offer-studio" in out_cta
        assert offer_id in out_cta
        assert "brand-studio" not in out_cta
