"""Unit tests for landing page content models and LandingPageConfig.

These are pure Pydantic validation tests — no DB required.
"""
import pytest
from datetime import datetime, timezone

from src.modules.landing.domain.content import (
    BrochureContent,
    EventContent,
    FeatureBullet,
    FlashOfferContent,
    LandingPageConfig,
    SqueezeContent,
    TransformerContent,
    VelvetRopeContent,
)
from src.modules.landing.domain.enums import LandingPageArchetype, LandingPageFont


class TestSqueezeContent:
    def test_squeeze_content_valid_required_fields(self):
        content = SqueezeContent(
            headline="Get the Free Guide",
            subheadline="Eliminate your biggest blocker",
            bullets=["Save time", "Save money", "Get results"],
        )
        assert content.headline == "Get the Free Guide"
        assert len(content.bullets) == 3

    def test_squeeze_content_defaults(self):
        content = SqueezeContent(
            headline="headline",
            subheadline="sub",
            bullets=["b1"],
        )
        assert content.cta_text == "Envíamelo ahora"
        assert content.privacy_text == "Tu información está segura."
        assert content.visual_url is None

    def test_squeeze_content_missing_headline_raises(self):
        with pytest.raises(Exception):
            SqueezeContent(
                subheadline="sub",
                bullets=["b1"],
            )

    def test_squeeze_content_missing_bullets_raises(self):
        with pytest.raises(Exception):
            SqueezeContent(
                headline="headline",
                subheadline="sub",
            )


class TestEventContent:
    def test_event_content_valid(self):
        event_date = datetime(2025, 6, 15, 18, 0, tzinfo=timezone.utc)
        content = EventContent(
            headline="Join the Live Webinar",
            event_date=event_date,
            hook_question="Are you tired of slow results?",
            secret_bullets=["Secret 1", "Secret 2", "Secret 3"],
            speaker_name="John Expert",
            speaker_bio="10+ years helping entrepreneurs",
        )
        assert content.speaker_name == "John Expert"
        assert content.event_date == event_date

    def test_event_content_missing_required_field_raises(self):
        with pytest.raises(Exception):
            EventContent(
                headline="headline",
                # missing event_date
                hook_question="question",
                secret_bullets=["s1"],
                speaker_name="Speaker",
                speaker_bio="Bio",
            )


class TestFlashOfferContent:
    def test_flash_offer_content_valid(self):
        content = FlashOfferContent(
            headline="Stop Struggling Today",
            offer_name="The Quick Fix Kit",
            problem_agitation="Every day without this costs you $500",
            solution_description="A fast, proven system",
            original_price=297.0,
            discounted_price=27.0,
        )
        assert content.original_price == 297.0
        assert content.discounted_price == 27.0
        assert content.guarantee_text == "30 días o devolución"

    def test_flash_offer_content_missing_prices_raises(self):
        with pytest.raises(Exception):
            FlashOfferContent(
                headline="headline",
                offer_name="offer",
                problem_agitation="pain",
                solution_description="solution",
                # missing prices
            )


class TestTransformerContent:
    def test_transformer_content_valid(self):
        content = TransformerContent(
            headline="6-Figure Coach in 90 Days",
            subheadline="Even starting from zero",
            problem_text="You're stuck trading time for money",
            agitation_text="This costs you thousands every month",
            solution_text="The system that changes everything",
            method_name="The Accelerator Method",
            method_description="A proven 3-phase approach",
            authority_name="Jane Expert",
            authority_bio="Helped 500+ clients",
            modules=[FeatureBullet(title="Module 1", description="Foundations")],
            price_anchor="$2,997",
            price_offer="$997",
            scarcity_text="Only 10 spots",
            cta_text="Join Now",
        )
        assert content.method_name == "The Accelerator Method"
        assert len(content.modules) == 1
        assert content.bonuses == []
        assert content.testimonials == []

    def test_transformer_content_bonuses_optional(self):
        content = TransformerContent(
            headline="h", subheadline="s", problem_text="p", agitation_text="a",
            solution_text="sol", method_name="M", method_description="md",
            authority_name="A", authority_bio="b",
            modules=[FeatureBullet(title="Mod 1")],
            price_anchor="$1k", price_offer="$500", scarcity_text="5 left",
        )
        assert content.bonuses == []
        assert content.story_hook is None


class TestVelvetRopeContent:
    def test_velvet_rope_content_valid(self):
        content = VelvetRopeContent(
            headline="Exclusive Inner Circle",
            manifesto_text="We believe in excellence and results",
            who_is_this_for=["Coaches earning $5k+/mo", "Serious entrepreneurs"],
            who_is_NOT_for=["Hobbyists", "Tire-kickers"],
            scarcity_text="Only 10 annual spots",
        )
        assert content.who_is_this_for == ["Coaches earning $5k+/mo", "Serious entrepreneurs"]
        assert content.experience_image_urls == []

    def test_velvet_rope_content_missing_manifesto_raises(self):
        with pytest.raises(Exception):
            VelvetRopeContent(
                headline="headline",
                # missing manifesto_text
                who_is_this_for=["a"],
                who_is_NOT_for=["b"],
                scarcity_text="limited",
            )


class TestBrochureContent:
    def test_brochure_content_valid(self):
        content = BrochureContent(
            headline="Grow Revenue by 3x in 6 Months",
            process_steps=[
                FeatureBullet(title="Discovery Call", description="We audit your funnel"),
                FeatureBullet(title="Strategy", description="Custom roadmap"),
            ],
            deliverables=["Monthly reports", "Weekly calls", "Slack access"],
        )
        assert len(content.process_steps) == 2
        assert content.authority_logos == []
        assert content.case_studies == []

    def test_brochure_content_missing_deliverables_raises(self):
        with pytest.raises(Exception):
            BrochureContent(
                headline="headline",
                process_steps=[FeatureBullet(title="Step 1")],
                # missing deliverables
            )


class TestFeatureBullet:
    def test_feature_bullet_required_title(self):
        bullet = FeatureBullet(title="Module 1: Foundation")
        assert bullet.title == "Module 1: Foundation"
        assert bullet.icon is None
        assert bullet.description is None

    def test_feature_bullet_full(self):
        bullet = FeatureBullet(icon="🎯", title="Core Skill", description="Master the fundamentals")
        assert bullet.icon == "🎯"


class TestLandingPageConfig:
    def test_config_with_squeeze_content(self):
        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug="my-page",
            content=SqueezeContent(
                headline="Get Free Access",
                subheadline="Start today",
                bullets=["Fast", "Easy", "Proven"],
            ),
        )
        assert config.archetype == LandingPageArchetype.THE_SQUEEZE
        assert config.is_published is False
        assert config.slug == "my-page"

    def test_config_default_theme(self):
        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_BROCHURE,
            slug="brochure-page",
            content=BrochureContent(
                headline="ROI-driven results",
                process_steps=[FeatureBullet(title="Step 1")],
                deliverables=["Report"],
            ),
        )
        assert config.theme.primary_color == "#000000"
        assert config.theme.font_pair == LandingPageFont.SANS_SERIF
        assert config.theme.dark_mode is False

    def test_config_accepts_dict_content(self):
        """Dict content (Puck editor data) is allowed without archetype validation."""
        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug="puck-page",
            content={"puck": True, "nodes": []},
        )
        assert isinstance(config.content, dict)

    def test_config_seo_fields_optional(self):
        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug="no-seo",
            content=SqueezeContent(
                headline="h", subheadline="s", bullets=["b1"],
            ),
        )
        assert config.seo_title is None
        assert config.seo_description is None

    def test_config_missing_slug_raises(self):
        with pytest.raises(Exception):
            LandingPageConfig(
                archetype=LandingPageArchetype.THE_SQUEEZE,
                # missing slug
                content=SqueezeContent(
                    headline="h", subheadline="s", bullets=["b1"],
                ),
            )
