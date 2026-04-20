"""Module Registry — Single source of truth for modules the copilot can introspect.

Each ModuleDescriptor declares HOW to read a module's data and model class.
The copilot never hardcodes field names; instead it uses the model_class for
Pydantic introspection and the repo/read functions for data access.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, cast

from pydantic import BaseModel

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
    from src.modules.commercial_calendar.infrastructure.repositories.calendar_event_repository import (
        CalendarEventRepository,
    )
    from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
        ChannelConnectionRepository,
    )
    from src.modules.landing.infrastructure.repositories.landing_repository import LandingRepository
    from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository
    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )


@dataclass
class ModuleDescriptor:
    """Metadata describing a module the copilot can read."""

    module_id: str  # "brand", "offer", etc.
    label: str  # "Brand Studio"
    description: str  # Short description for system prompt
    route_prefix: str  # Route segment for matching (e.g. "brand-settings")

    # Optional Pydantic model — enables automatic introspection of sections/fields.
    # Not all modules have a single root model (e.g. analytics uses SQL queries).
    model_class: type[BaseModel] | None = None

    # Factory: (db_session) -> repository_instance
    repo_factory: Callable | None = None

    # Read function: (repo, tenant_id) -> data (model instance or dict/list)
    read_fn: Callable | None = None

    # Extra keywords for fuzzy matching
    keywords: list[str] = field(default_factory=list)


def _build_registry() -> dict[str, ModuleDescriptor]:
    """Build the registry lazily to avoid circular imports at module load time."""
    return {
        "brand": ModuleDescriptor(
            module_id="brand",
            label="Brand Studio",
            description=(
                "Identidad de marca completa: nombre, historia, posicionamiento (Brand Love Key),"
                " narrativa (StoryBrand), identidad visual, voz, equipo, testimonios, autoridad, assets de comunicación"
            ),
            route_prefix="brand-studio",
            model_class=_lazy_brand_settings(),
            repo_factory=_brand_repo_factory,
            read_fn=_brand_read_fn,
            keywords=["marca", "brand", "identidad", "posicionamiento", "narrativa"],
        ),
        "offer": ModuleDescriptor(
            module_id="offer",
            label="Offer Studio",
            description=(
                "Escalera de ofertas: productos/servicios con precio,"
                " psicología de venta, avatar, objeciones, knowledge base"
            ),
            route_prefix="offer-studio",
            model_class=None,  # Offers are SQLAlchemy rows, not a single Pydantic root
            repo_factory=_offer_repo_factory,
            read_fn=_offer_read_fn,
            keywords=["oferta", "producto", "servicio", "precio", "escalera"],
        ),
        "connections": ModuleDescriptor(
            module_id="connections",
            label="Conexiones",
            description=(
                "Integraciones externas: Meta, Instagram, WhatsApp, Shopify,"
                " Google Calendar, Gmail, Mailerlite, YouTube, Google Analytics, Google Ads"
            ),
            route_prefix="connections",
            model_class=None,
            repo_factory=_connections_repo_factory,
            read_fn=_connections_read_fn,
            keywords=[
                "conexión",
                "integración",
                "meta",
                "instagram",
                "whatsapp",
                "shopify",
            ],
        ),
        "crm": ModuleDescriptor(
            module_id="crm",
            label="CRM",
            description="Leads, clientes y ventas: pipeline, scoring, temperatura, historial de compras",
            route_prefix="sales",
            model_class=None,
            repo_factory=None,  # Uses multiple repos — handled by dedicated tools
            read_fn=None,
            keywords=["lead", "cliente", "venta", "pipeline", "CRM"],
        ),
        "analytics": ModuleDescriptor(
            module_id="analytics",
            label="Growth Studio",
            description="Métricas de marketing y ventas: funnel bowtie, conversión, revenue, leads por etapa",
            route_prefix="growth-studio",
            model_class=None,
            repo_factory=None,  # Uses SalesMetricsRepository — handled by dedicated tool
            read_fn=None,
            keywords=[
                "funnel",
                "bowtie",
                "métricas",
                "analytics",
                "growth",
                "conversión",
            ],
        ),
        "sales_agent": ModuleDescriptor(
            module_id="sales_agent",
            label="Sales Agent",
            description="Agente de ventas IA: conversaciones activas, mensajes, rendimiento",
            route_prefix="sales",
            model_class=None,
            repo_factory=None,
            read_fn=None,
            keywords=["agente", "ventas", "conversación", "chat", "SDR"],
        ),
        "commercial_calendar": ModuleDescriptor(
            module_id="commercial_calendar",
            label="Calendario Comercial",
            description=(
                "Eventos del calendario comercial: feriados nacionales, campanas,"
                " temporadas de venta, dias especiales. Eventos del sistema + eventos custom por tenant."
            ),
            route_prefix="commercial-calendar",
            model_class=None,  # CalendarEvent is a dataclass, not Pydantic
            repo_factory=_calendar_repo_factory,
            read_fn=_calendar_read_fn,
            keywords=[
                "calendario",
                "feriado",
                "campana",
                "temporada",
                "cyber",
                "holiday",
                "sale",
            ],
        ),
        "landing": ModuleDescriptor(
            module_id="landing",
            label="Landing Pages",
            description="Páginas de aterrizaje: generadas automáticamente o personalizadas, vinculadas a ofertas",
            route_prefix="landing",
            model_class=None,
            repo_factory=_landing_repo_factory,
            read_fn=_landing_read_fn,
            keywords=["landing", "página", "aterrizaje"],
        ),
        "social_proof": ModuleDescriptor(
            module_id="social_proof",
            label="Social Proof Studio",
            description=(
                "Prueba social tenant-scoped: testimonios de clientes, autoridades"
                " / certificaciones / premios, equipo (voz de marca). Se reutiliza"
                " cross-surface (brand, offer, landing, email, sales agent) via"
                " placements M:N — editar un testimonio se propaga automáticamente."
            ),
            route_prefix="social-proof",
            model_class=None,  # 3 roots — consumers iterate via read_fn per collection
            repo_factory=_social_proof_repo_factory,
            read_fn=_social_proof_read_fn,
            keywords=[
                "testimonios",
                "testimonio",
                "autoridad",
                "authority",
                "certificaciones",
                "equipo",
                "team",
                "prueba social",
                "confianza",
                "credibilidad",
            ],
        ),
    }


# ── Lazy loaders (avoid circular imports) ─────────────────────────────


def _lazy_brand_settings() -> type[BaseModel]:
    """Return BrandSettings class — imported lazily."""
    from src.modules.brand.domain.aggregates import BrandSettings

    return BrandSettings


def _brand_repo_factory(db: object) -> object:
    from src.modules.brand.infrastructure.repositories.brand_repository import (
        BrandRepository,
    )

    return BrandRepository(db)


def _brand_read_fn(repo: object, tenant_id: UUID) -> object | None:
    return cast("BrandRepository", repo).get_settings(tenant_id)


def _offer_repo_factory(db: object) -> object:
    from src.modules.offer.infrastructure.repositories.offer_repository import (
        OfferRepository,
    )

    return OfferRepository(db)


def _offer_read_fn(repo: object, tenant_id: UUID) -> list:
    return cast("OfferRepository", repo).get_all_by_tenant(tenant_id)


def _connections_repo_factory(db: object) -> object:
    from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
        ChannelConnectionRepository,
    )

    return ChannelConnectionRepository(db)


def _connections_read_fn(repo: object, tenant_id: UUID) -> list:
    return cast("ChannelConnectionRepository", repo).get_all_by_tenant(tenant_id)


def _calendar_repo_factory(db: object) -> object:
    from src.modules.commercial_calendar.infrastructure.repositories.calendar_event_repository import (
        CalendarEventRepository,
    )

    return CalendarEventRepository(db)


def _calendar_read_fn(repo: object, tenant_id: UUID) -> list:
    from src.shared.domain.datetime_utils import utc_today

    today = utc_today()
    return cast("CalendarEventRepository", repo).list_events(
        country_code="PE",
        year=today.year,
        tenant_id=tenant_id,
    )


def _landing_repo_factory(db: object) -> object:
    from src.modules.landing.infrastructure.repositories.landing_repository import (
        LandingRepository,
    )

    return LandingRepository(db)


def _landing_read_fn(repo: object, tenant_id: UUID) -> list:
    return cast("LandingRepository", repo).list_by_tenant(tenant_id)


def _social_proof_repo_factory(db: object) -> object:
    """Return a bundle of repos — ``read_fn`` iterates all 3 collections."""
    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )

    return {
        "testimonials": TestimonialRepository(db),
        "authority_items": AuthorityItemRepository(db),
        "team_members": TeamMemberRepository(db),
    }


def _social_proof_read_fn(repo: object, tenant_id: UUID) -> dict:
    """Return the 3 collections keyed by source table — Copilot fans out."""
    bundle = cast("dict", repo)
    testimonials_repo = cast("TestimonialRepository", bundle["testimonials"])
    authority_repo = cast("AuthorityItemRepository", bundle["authority_items"])
    team_repo = cast("TeamMemberRepository", bundle["team_members"])
    return {
        "testimonials": testimonials_repo.list_by_tenant(tenant_id),
        "authority_items": authority_repo.list_by_tenant(tenant_id),
        "team_members": team_repo.list_by_tenant(tenant_id),
    }


# ── Singleton ─────────────────────────────────────────────────────────


@functools.lru_cache(maxsize=1)
def get_module_registry() -> dict[str, ModuleDescriptor]:
    """Return the module registry, building it on first access."""
    return _build_registry()
