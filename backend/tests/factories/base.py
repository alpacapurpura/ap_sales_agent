"""
Test factories for Nicolify.

Usage:
    from tests.factories import TenantFactory, BrandSettingsFactory

    # ORM model — add to db session manually:
    tenant = TenantFactory()
    db.add(tenant)
    db.commit()

    # Domain model (Pydantic) — use directly:
    settings = BrandSettingsFactory()
"""
import uuid

import factory
from faker import Faker

from src.modules.brand.domain import (
    Avatar,
    BrandIdentity,
    BrandSettings,
    BrandStory,
    BrandVisuals,
)

fake = Faker()


# ---------------------------------------------------------------------------
# IAM — builds TenantModel instances without triggering SA mapper config
# ---------------------------------------------------------------------------

class TenantFactory(factory.Factory):
    class Meta:
        model = dict

    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("company")
    slug = factory.LazyAttribute(
        lambda o: f"{o.name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
    )
    config_json = factory.LazyFunction(dict)
    is_active = True

    @classmethod
    def _build(cls, model_class, **kwargs):
        """Build a TenantModel instance. Import related models first to
        satisfy SQLAlchemy's lazy relationship resolution."""
        # These imports register models so SA can resolve relationship strings
        from src.modules.crm.infrastructure.models.lead_model import LeadModel  # noqa: F401
        from src.modules.crm.infrastructure.models.lifecycle_transition_model import LifecycleTransitionModel  # noqa: F401
        from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel  # noqa: F401
        from src.modules.sales_agent.infrastructure.models.message_model import MessageModel  # noqa: F401
        from src.modules.scheduling.infrastructure.models.appointment_model import AppointmentModel  # noqa: F401
        from src.modules.crm.infrastructure.models.sale_model import SaleModel  # noqa: F401
        from src.modules.offer.infrastructure.models.product_model import ProductModel  # noqa: F401
        from src.modules.brand.infrastructure.models.avatar_model import AvatarModel as AvatarORM  # noqa: F401
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel
        return TenantModel(**kwargs)

    @classmethod
    def _create(cls, model_class, **kwargs):
        return cls._build(model_class, **kwargs)


# ---------------------------------------------------------------------------
# Brand — Domain models (Pydantic, not ORM)
# ---------------------------------------------------------------------------

class BrandIdentityFactory(factory.Factory):
    class Meta:
        model = BrandIdentity

    brand_name = factory.Faker("company")
    tagline = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph", nb_sentences=2)
    industry = factory.Faker(
        "random_element",
        elements=["Technology", "Health", "Education", "Finance", "E-commerce"],
    )
    website = factory.Faker("url")
    founding_year = factory.Faker(
        "random_element", elements=["2018", "2019", "2020", "2021", "2022", "2023"]
    )


class BrandVisualsFactory(factory.Factory):
    class Meta:
        model = BrandVisuals

    primary_color = factory.Faker("hex_color")
    secondary_color = factory.Faker("hex_color")
    accent_color = factory.Faker("hex_color")
    background_color = "#ffffff"
    font_heading = factory.Faker(
        "random_element", elements=["Inter", "Poppins", "Montserrat", "DM Sans"]
    )
    font_body = factory.Faker(
        "random_element", elements=["Inter", "Open Sans", "Lato", "Source Sans Pro"]
    )


class BrandStoryFactory(factory.Factory):
    class Meta:
        model = BrandStory

    origin_story = factory.Faker("paragraph", nb_sentences=3)
    mission = factory.Faker("sentence")
    vision = factory.Faker("sentence")


class BrandSettingsFactory(factory.Factory):
    class Meta:
        model = BrandSettings

    identity = factory.SubFactory(BrandIdentityFactory)
    visuals = factory.SubFactory(BrandVisualsFactory)
    story = factory.SubFactory(BrandStoryFactory)
    team = factory.LazyFunction(list)
    testimonials = factory.LazyFunction(list)
    authority_vault = factory.LazyFunction(list)


class AvatarFactory(factory.Factory):
    class Meta:
        model = Avatar

    id = factory.LazyFunction(uuid.uuid4)
    tenant_id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("job")
    scope = "GLOBAL"
    icp_description = factory.Faker("paragraph", nb_sentences=2)
    anti_avatar = factory.Faker("sentence")
    is_default = False
