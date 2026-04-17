"""Domain tests for ``LandingPage.edition_id`` binding (Phase 3).

A landing may be offer-level (``edition_id IS NULL`` — template fallback)
or edition-scoped (``edition_id`` set — belongs to a specific launch
edition). These tests nail down that contract at the domain layer so the
repository and service code can rely on it.
"""

from __future__ import annotations

from uuid import uuid4

from src.modules.landing.domain.content import (
    LandingPageConfig,
    SqueezeContent,
)
from src.modules.landing.domain.enums import LandingPageArchetype
from src.modules.landing.domain.landing_page import LandingPage


def _make_config(slug: str = "edition-test") -> LandingPageConfig:
    return LandingPageConfig(
        archetype=LandingPageArchetype.THE_SQUEEZE,
        content=SqueezeContent(
            headline="Headline",
            subheadline="Subheadline",
            bullets=["b1", "b2", "b3"],
        ),
        slug=slug,
    )


class TestLandingPageEditionBinding:
    def test_offer_level_landing_has_no_edition_id(self) -> None:
        landing = LandingPage(
            id=uuid4(),
            tenant_id=uuid4(),
            offer_id=uuid4(),
            slug="offer-level",
            config=_make_config("offer-level"),
        )
        assert landing.edition_id is None

    def test_edition_scoped_landing_sets_edition_id(self) -> None:
        edition_id = uuid4()
        landing = LandingPage(
            id=uuid4(),
            tenant_id=uuid4(),
            offer_id=uuid4(),
            edition_id=edition_id,
            slug="edition-scoped",
            config=_make_config("edition-scoped"),
        )
        assert landing.edition_id == edition_id
