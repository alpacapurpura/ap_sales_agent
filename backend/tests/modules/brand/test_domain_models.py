"""Tests for Brand Studio domain models -- Pydantic validation, defaults, migration."""

from src.modules.brand.domain import (
    BrandBenefits,
    BrandContact,
    BrandIdentity,
    BrandMethodologyPillar,
    BrandNarrative,
    BrandPositioning,
    BrandSettings,
    BrandStory,
    BrandStoryMilestone,
    BrandStrategy,
    BrandTestimonial,
    BrandValues,
    BrandVisuals,
    CommunicationAssets,
    CompetitiveEnvironment,
    ConsumerInsight,
    FunnelAsset,
    KeyFigure,
    ReasonToBelieve,
    StoryBrandCTA,
    StoryBrandGuide,
    StoryBrandHero,
    StoryBrandOutcome,
    StoryBrandPlanStep,
    StoryBrandProblem,
)


class TestBrandSettings:
    """Root aggregate: BrandSettings."""

    def test_empty_construction(self):
        s = BrandSettings()
        assert s.identity is None
        assert s.story is None
        assert s.team == []
        assert s.testimonials == []
        assert s.authority_vault == []

    def test_full_construction(self, sample_settings):
        assert sample_settings.identity.brand_name == "TestBrand"
        assert sample_settings.visuals.primary_color == "#0f172a"

    def test_extra_fields_ignored(self):
        s = BrandSettings(nonexistent_field="hello")
        assert not hasattr(s, "nonexistent_field")

    def test_migration_strategy_to_positioning(self):
        """Legacy: unique_value_proposition moves from strategy to positioning."""
        data = {
            "strategy": {
                "unique_value_proposition": "We are the best",
                "competitors": [
                    {"id": "1", "name": "Rival", "differentiation": "cheap"},
                ],
                "methodology_name": "Test Method",
            },
        }
        s = BrandSettings(**data)
        assert s.positioning is not None
        assert s.positioning.unique_value_proposition == "We are the best"
        assert s.positioning.competitive_environment is not None
        assert len(s.positioning.competitive_environment.direct_competitors) == 1

    def test_migration_preserves_existing_positioning(self):
        """Migration does NOT overwrite existing positioning fields."""
        data = {
            "strategy": {"unique_value_proposition": "old"},
            "positioning": {
                "unique_value_proposition": "keep this",
                "brand_essence": "core",
            },
        }
        s = BrandSettings(**data)
        assert s.positioning.unique_value_proposition == "keep this"
        assert s.positioning.brand_essence == "core"

    def test_roundtrip_json(self, sample_settings):
        dumped = sample_settings.model_dump(mode="json")
        restored = BrandSettings.model_validate(dumped)
        assert restored.identity.brand_name == "TestBrand"
        assert restored.visuals.primary_color == "#0f172a"


class TestBrandIdentity:
    def test_minimal(self):
        i = BrandIdentity(brand_name="X")
        assert i.brand_name == "X"
        assert i.tagline is None

    def test_full(self, sample_identity):
        assert sample_identity.industry == "Technology"

    def test_business_types_default_empty_list(self):
        """A fresh brand has no business types declared yet — onboarding fills them."""
        i = BrandIdentity(brand_name="X")
        assert i.business_types == []

    def test_business_types_accepts_multi_select(self):
        """Multi-select: a course creator who also coaches declares both."""
        from src.shared.domain.expert_business_type import ExpertBusinessType

        i = BrandIdentity(
            brand_name="X",
            business_types=[
                ExpertBusinessType.ACADEMIA_INFOPRODUCTOR,
                ExpertBusinessType.COACH_MENTOR,
            ],
        )
        assert len(i.business_types) == 2
        assert ExpertBusinessType.COACH_MENTOR in i.business_types

    def test_business_types_roundtrip_json(self):
        """JSON persistence (tenant.config_json blob) must preserve values."""
        from src.shared.domain.expert_business_type import ExpertBusinessType

        original = BrandIdentity(
            brand_name="X",
            business_types=[ExpertBusinessType.SOFTWARE_SAAS],
        )
        dumped = original.model_dump(mode="json")
        restored = BrandIdentity.model_validate(dumped)
        assert restored.business_types == [ExpertBusinessType.SOFTWARE_SAAS]

    def test_business_types_drops_unknown_values_silently(self):
        """Unknown values are dropped (not raised) to prevent crashing
        brand-settings reads on config_json saved with stale vocabulary.

        Sprint 14: the validator now silently drops unknown keys. See
        ``_normalise_business_types`` — the rationale is that failing
        to load blocks onboarding entirely; dropping lets the dialog
        render and the user re-saves a clean list.
        """
        from src.shared.domain.expert_business_type import ExpertBusinessType

        identity = BrandIdentity(
            brand_name="X",
            business_types=["coach_mentor", "nonexistent_type"],
        )
        assert identity.business_types == [ExpertBusinessType.COACH_MENTOR]

    def test_business_types_remaps_legacy_aliases(self):
        """Legacy enum values map to their canonical replacement."""
        from src.shared.domain.expert_business_type import ExpertBusinessType

        identity = BrandIdentity(
            brand_name="X",
            business_types=["consultor_asesor", "educador_infoproductor", "creador_contenido"],
        )
        assert identity.business_types == [
            ExpertBusinessType.CONSULTOR_PROFESIONAL,
            ExpertBusinessType.ACADEMIA_INFOPRODUCTOR,
        ]


class TestBrandVisuals:
    def test_defaults(self):
        v = BrandVisuals()
        assert v.primary_color is None
        assert v.color_palette == []

    def test_with_colors(self, sample_visuals):
        assert sample_visuals.accent_color == "#3b82f6"


class TestBrandStory:
    def test_empty_milestones(self):
        s = BrandStory(origin_story="test")
        assert s.milestones == []

    def test_with_milestones(self):
        m = BrandStoryMilestone(
            id="1",
            year="2020",
            title="Founded",
            description="Started",
        )
        s = BrandStory(milestones=[m])
        assert len(s.milestones) == 1
        assert s.milestones[0].year == "2020"


class TestBrandStrategy:
    def test_empty(self):
        s = BrandStrategy()
        assert s.methodology_name is None
        assert s.methodology_pillars == []

    def test_with_pillars(self):
        p = BrandMethodologyPillar(id="1", title="Pillar1", description="Desc")
        s = BrandStrategy(methodology_name="Method", methodology_pillars=[p])
        assert len(s.methodology_pillars) == 1


class TestBrandContact:
    def test_legacy_email_migration(self):
        """Legacy: 'email' field migrates to 'support_email'."""
        c = BrandContact(email="old@test.com")
        assert c.support_email == "old@test.com"

    def test_modern_fields(self):
        c = BrandContact(support_email="new@test.com", social_instagram="@brand")
        assert c.support_email == "new@test.com"
        assert c.social_instagram == "@brand"


class TestBrandTestimonial:
    def test_legacy_migration(self):
        """Legacy: 'author', 'role', 'quote' migrate to new field names."""
        t = BrandTestimonial(author="John", role="CEO", quote="Great!")
        assert t.author_name == "John"
        assert t.author_role == "CEO"
        assert t.content == "Great!"


class TestKeyFigure:
    def test_minimal(self):
        k = KeyFigure(id="1", name="Alice", role="CTO")
        assert k.name == "Alice"
        assert k.gallery == []


class TestBrandPositioning:
    def test_empty(self):
        p = BrandPositioning()
        assert p.brand_essence is None
        assert p.reasons_to_believe == []

    def test_full_brand_love_key(self):
        p = BrandPositioning(
            competitive_environment=CompetitiveEnvironment(
                technical_enemy="Legacy tools",
                philosophical_enemy="Complexity",
            ),
            insight=ConsumerInsight(
                tension="Need simplicity",
                observation="Tools are complex",
            ),
            benefits=BrandBenefits(
                functional_benefits=["Fast"],
                emotional_benefits=["Calm"],
            ),
            values=BrandValues(core_values=["Innovation"], personality_traits=["Bold"]),
            reasons_to_believe=[
                ReasonToBelieve(id="1", type="dato", statement="99% uptime"),
            ],
            discriminator="Only AI-native solution",
            brand_essence="Simplicity",
            unique_value_proposition="AI that works",
        )
        assert p.brand_essence == "Simplicity"
        assert len(p.reasons_to_believe) == 1


class TestBrandNarrative:
    def test_storybrand_structure(self):
        n = BrandNarrative(
            hero=StoryBrandHero(identity="Entrepreneur", desire="Grow"),
            problem=StoryBrandProblem(villain="Complexity"),
            guide=StoryBrandGuide(empathy_statement="We understand"),
            plan=[StoryBrandPlanStep(id="1", step_number=1, title="Step 1")],
            cta=StoryBrandCTA(direct_cta="Buy now"),
            outcome=StoryBrandOutcome(success_transformation="Growth"),
            one_liner="We help entrepreneurs grow by simplifying complexity",
        )
        assert n.hero.identity == "Entrepreneur"
        assert len(n.plan) == 1


class TestCommunicationAssets:
    def test_empty(self):
        ca = CommunicationAssets()
        assert ca.creative_concepts == []
        assert ca.assets == []

    def test_with_funnel_assets(self):
        fa = FunnelAsset(
            id="1",
            funnel_stage="TOFU",
            asset_type="reel",
            title="Intro Video",
            idea="Show product",
            objective="Awareness",
        )
        ca = CommunicationAssets(assets=[fa])
        assert len(ca.assets) == 1
        assert ca.assets[0].funnel_stage == "TOFU"


class TestAvatar:
    def test_construction(self, sample_avatar):
        assert sample_avatar.name == "Ideal Customer"
        assert sample_avatar.scope == "GLOBAL"
        assert sample_avatar.is_default is False
