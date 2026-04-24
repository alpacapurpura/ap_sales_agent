"""Golden baseline for reference offer ``a96403b5-c1db-4b31-97aa-cb18d08ad9f9``.

Acts as the anti-regression gate for the multi-sprint
``docs/refactors/field-contract-ssot/`` refactor. Every phase must keep this
test green; additive changes (new fields on ``Offer`` / ``LandingPageConfig``)
are allowed as long as the fixture still round-trips.

Regenerate the fixture via
``backend/scripts/capture_offer_a96403b5_baseline.py`` after an intentional
architectural change. See ``docs/refactors/field-contract-ssot/fixtures/offer_a96403b5_baseline.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.modules.landing.domain.content import LandingPageConfig
from src.modules.offer.domain.offer import Offer

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "offer_a96403b5_baseline.json"

REFERENCE_TENANT_ID = "1fd1562b-2101-410a-870c-dc2f7e27b355"
REFERENCE_OFFER_ID = "a96403b5-c1db-4b31-97aa-cb18d08ad9f9"


@pytest.fixture(scope="module")
def baseline() -> dict:
    assert FIXTURE_PATH.exists(), (
        f"Missing golden fixture {FIXTURE_PATH}. Regenerate with scripts/capture_offer_a96403b5_baseline.py."
    )
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_baseline_meta_points_to_reference_offer(baseline: dict) -> None:
    meta = baseline["_meta"]
    assert meta["tenant_id"] == REFERENCE_TENANT_ID
    assert meta["offer_id"] == REFERENCE_OFFER_ID


def test_offer_state_round_trips_through_pydantic(baseline: dict) -> None:
    """Schema-drift detector — Offer must still validate the captured payload."""
    Offer.model_validate(baseline["offer_db_state"])


def test_rendered_prompt_carries_offer_identity(baseline: dict) -> None:
    prompt = baseline["rendered_identity_prompt"]
    assert isinstance(prompt, str) and prompt.strip(), "Prompt must be non-empty."
    public_name = baseline["offer_db_state"]["public_name"]
    assert public_name in prompt, f"Public name {public_name!r} disappeared from rendered agent identity."


def test_landing_config_round_trips_through_pydantic(baseline: dict) -> None:
    LandingPageConfig.model_validate(baseline["landing_config"])


def test_landing_config_preserves_offer_naming(baseline: dict) -> None:
    landing = baseline["landing_config"]
    public_name = baseline["offer_db_state"]["public_name"]
    assert landing["seo_title"] == public_name
    assert REFERENCE_OFFER_ID[:8] in landing["slug"]
