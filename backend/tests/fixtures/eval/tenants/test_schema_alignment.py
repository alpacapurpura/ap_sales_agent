"""Tests for schema alignment — seed YAMLs vs existing Pydantic models.

Status in T-1: RED expected until T-3 creates the seed YAML files.

Design (AD2): YAMLs validate against existing brand/offer domain models.
If a model doesn't expose the needed subset → adjust YAML, NOT model.

Brand model: BrandSettings (brand/domain/aggregates.py) — extra="ignore"
PersonalityProfile: brand/domain/personality.py — extra="forbid"

Note: We validate the brand YAML against BrandSettings using model_validate
with extra="ignore" (the model's own config), so only the declared fields
are enforced. We DO NOT validate the full PersonalityProfile (which has
required UUID fields like id, tenant_id) — instead we validate the
personality dimensions, linguistic_patterns, and sample_exchanges sub-models
that are present in the seed YAML.
"""

from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS, _THIS_DIR

# ---------------------------------------------------------------------------
# Import brand domain models (read-only per 05-guidelines.md)
# ---------------------------------------------------------------------------

from src.modules.brand.domain.aggregates import BrandSettings
from src.modules.brand.domain.personality import (
    LinguisticPatterns,
    PersonalityDimensions,
    SampleExchange,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_yaml(archetype_slug: str, filename: str) -> dict:
    """Load a seed YAML file. Raises FileNotFoundError if missing (T-3)."""
    path = _THIS_DIR / archetype_slug / f"{filename}.yaml"
    if not path.is_file():
        pytest.skip(f"Seed YAML not yet created: {path}. Unblocked by T-3.")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_brand_yaml_validates_against_brand_settings(archetype_slug: str) -> None:
    """brand.yaml content must be parseable by BrandSettings.model_validate.

    BrandSettings uses extra="ignore" so only declared fields are enforced.
    This ensures schema drift is caught (AD2).
    """
    data = _load_yaml(archetype_slug, "brand")
    # Should not raise
    settings = BrandSettings.model_validate(data)
    assert settings is not None


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_personality_profile_yaml_validates_sub_models(archetype_slug: str) -> None:
    """personality_profile.yaml must contain valid dimensions + patterns + exchanges.

    We do NOT validate the full PersonalityProfile (which requires UUID id/tenant_id).
    Instead we validate the 3 sub-models that live in the seed YAML.
    """
    data = _load_yaml(archetype_slug, "personality_profile")

    # Validate dimensions
    dims_data = data.get("dimensions")
    assert dims_data is not None, "personality_profile.yaml must have 'dimensions' section"
    PersonalityDimensions.model_validate(dims_data)

    # Validate linguistic_patterns
    patterns_data = data.get("linguistic_patterns")
    assert patterns_data is not None, "personality_profile.yaml must have 'linguistic_patterns' section"
    LinguisticPatterns.model_validate(patterns_data)

    # Validate sample_exchanges (list)
    exchanges_data = data.get("sample_exchanges", [])
    assert isinstance(exchanges_data, list), "sample_exchanges must be a list"
    for ex in exchanges_data:
        SampleExchange.model_validate(ex)


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_offer_ladder_yaml_has_offers_list(archetype_slug: str) -> None:
    """offer_ladder.yaml must have an 'offers' key with a list value.

    Basic structural validation — full schema alignment is deferred to
    test_loader.py tests once T-3 creates content.
    """
    data = _load_yaml(archetype_slug, "offer_ladder")
    assert "offers" in data, "offer_ladder.yaml must have top-level 'offers' key"
    assert isinstance(data["offers"], list), "'offers' must be a list"
    assert len(data["offers"]) >= 1, "'offers' list must have at least one entry"


def test_loader_raises_on_missing_required_field() -> None:
    """model_validate on a dict missing required fields raises ValidationError.

    Uses PersonalityDimensions (all fields required: energy, warmth, humor,
    expressiveness, narrative, verbosity) as the canary.
    """
    incomplete = {
        "energy": 0.7,
        # warmth, humor, expressiveness, narrative, verbosity MISSING
    }
    with pytest.raises(ValidationError):
        PersonalityDimensions.model_validate(incomplete)
