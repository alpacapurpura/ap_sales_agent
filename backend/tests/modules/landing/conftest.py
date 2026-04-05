"""Fixtures for landing module tests."""

import pytest


@pytest.fixture
def sample_squeeze_config_dict():
    """Minimal valid LandingPageConfig dict for THE_SQUEEZE archetype."""
    return {
        "archetype": "THE_SQUEEZE",
        "slug": "my-squeeze-page",
        "content": {
            "headline": "Grab This Free Guide",
            "subheadline": "No more struggling with X",
            "bullets": ["Benefit 1", "Benefit 2", "Benefit 3"],
            "cta_text": "Send it now",
            "privacy_text": "Your data is safe.",
        },
    }


@pytest.fixture
def sample_transformer_config_dict():
    """Minimal valid LandingPageConfig dict for THE_TRANSFORMER archetype."""
    return {
        "archetype": "THE_TRANSFORMER",
        "slug": "my-transformer-page",
        "content": {
            "headline": "Become a 6-Figure Coach in 90 Days",
            "subheadline": "Even if you're starting from zero",
            "problem_text": "You're tired of trading time for money",
            "agitation_text": "Every month without a system costs you thousands",
            "solution_text": "The Accelerator Method gets you there fast",
            "method_name": "The Accelerator Method",
            "method_description": "A 3-phase system proven to work",
            "authority_name": "Jane Doe",
            "authority_bio": "Helped 500+ coaches scale to 6-figures",
            "modules": [
                {"title": "Module 1: Foundations", "description": "Build your base"},
            ],
            "price_anchor": "$2,997",
            "price_offer": "$997",
            "scarcity_text": "Only 10 spots left",
            "cta_text": "Join now",
        },
    }
