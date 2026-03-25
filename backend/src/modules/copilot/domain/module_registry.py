"""
Module Registry — Single source of truth for modules the copilot can introspect.

Each ModuleDescriptor declares HOW to read a module's data and model class.
The copilot never hardcodes field names; instead it uses the model_class for
Pydantic introspection and the repo/read functions for data access.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type

from pydantic import BaseModel


@dataclass
class ModuleDescriptor:
    """Metadata describing a module the copilot can read."""

    module_id: str  # "brand", "offer", etc.
    label: str  # "Brand Studio"
    description: str  # Short description for system prompt
    route_prefix: str  # Route segment for matching (e.g. "brand-settings")

    # Optional Pydantic model — enables automatic introspection of sections/fields.
    # Not all modules have a single root model (e.g. analytics uses SQL queries).
    model_class: Optional[Type[BaseModel]] = None

    # Factory: (db_session) -> repository_instance
    repo_factory: Optional[Callable] = None

    # Read function: (repo, tenant_id) -> data (model instance or dict/list)
    read_fn: Optional[Callable] = None

    # Extra keywords for fuzzy matching
    keywords: List[str] = field(default_factory=list)


def _build_registry() -> Dict[str, ModuleDescriptor]:
    """Build the registry lazily to avoid circular imports at module load time."""
    return {
        "brand": ModuleDescriptor(
            module_id="brand",
            label="Brand Studio",
            description="Identidad de marca completa: nombre, historia, posicionamiento (Brand Love Key), narrativa (StoryBrand), identidad visual, voz, equipo, testimonios, autoridad, assets de comunicación",
            route_prefix="brand-settings",
            model_class=_lazy_brand_settings(),
            repo_factory=_brand_repo_factory,
            read_fn=_brand_read_fn,
            keywords=["marca", "brand", "identidad", "posicionamiento", "narrativa"],
        ),
        "offer": ModuleDescriptor(
            module_id="offer",
            label="Offer Studio",
            description="Escalera de ofertas: productos/servicios con precio, psicología de venta, avatar, objeciones, knowledge base",
            route_prefix="offer-studio",
            model_class=None,  # Offers are SQLAlchemy rows, not a single Pydantic root
            repo_factory=_offer_repo_factory,
            read_fn=_offer_read_fn,
            keywords=["oferta", "producto", "servicio", "precio", "escalera"],
        ),
        "connections": ModuleDescriptor(
            module_id="connections",
            label="Conexiones",
            description="Integraciones externas: Meta, Instagram, WhatsApp, Shopify, Google Calendar, Gmail, Mailerlite, YouTube, Google Analytics, Google Ads",
            route_prefix="connections",
            model_class=None,
            repo_factory=_connections_repo_factory,
            read_fn=_connections_read_fn,
            keywords=["conexión", "integración", "meta", "instagram", "whatsapp", "shopify"],
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
            route_prefix="marketing-studio",
            model_class=None,
            repo_factory=None,  # Uses SalesMetricsRepository — handled by dedicated tool
            read_fn=None,
            keywords=["funnel", "bowtie", "métricas", "analytics", "growth", "conversión"],
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
    }


# ── Lazy loaders (avoid circular imports) ─────────────────────────────


def _lazy_brand_settings():
    """Return BrandSettings class — imported lazily."""
    from src.modules.brand.domain.aggregates import BrandSettings
    return BrandSettings


def _brand_repo_factory(db):
    from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
    return BrandRepository(db)


def _brand_read_fn(repo, tenant_id):
    return repo.get_settings(tenant_id)


def _offer_repo_factory(db):
    from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository
    return OfferRepository(db)


def _offer_read_fn(repo, tenant_id):
    return repo.get_all_by_tenant(tenant_id)


def _connections_repo_factory(db):
    from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
        ChannelConnectionRepository,
    )
    return ChannelConnectionRepository(db)


def _connections_read_fn(repo, tenant_id):
    return repo.get_all_by_tenant(tenant_id)


def _landing_repo_factory(db):
    from src.modules.landing.infrastructure.repositories.landing_repository import LandingRepository
    return LandingRepository(db)


def _landing_read_fn(repo, tenant_id):
    return repo.list_by_tenant(tenant_id)


# ── Singleton ─────────────────────────────────────────────────────────

_registry: Optional[Dict[str, ModuleDescriptor]] = None


def get_module_registry() -> Dict[str, ModuleDescriptor]:
    """Return the module registry, building it on first access."""
    global _registry
    if _registry is None:
        _registry = _build_registry()
    return _registry
