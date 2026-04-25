"""Brand module data — descriptor + lazy repo accessors.

Lifted verbatim from the legacy ``copilot/domain/module_registry.py`` to remove
the ``copilot → brand`` import. The copilot now consumes brand metadata via
``BrandCopilotProvider.module_data()``; the legacy registry is a thin shim
that delegates to the discovered providers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.modules.copilot.domain.ports import ModuleData

if TYPE_CHECKING:
    from uuid import UUID

    from pydantic import BaseModel

    from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository


def _lazy_brand_settings() -> type[BaseModel]:
    """Return the BrandSettings class — imported lazily to dodge module-load cycles."""
    from src.modules.brand.domain.aggregates import BrandSettings

    return BrandSettings


def _brand_repo_factory(db: object) -> object:
    from src.modules.brand.infrastructure.repositories.brand_repository import (
        BrandRepository,
    )

    return BrandRepository(db)


def _brand_read_fn(repo: object, tenant_id: UUID) -> object | None:
    return cast("BrandRepository", repo).get_settings(tenant_id)


def build_brand_module_data() -> ModuleData:
    """Return the ``ModuleData`` record for the brand module."""
    return ModuleData(
        module_id="brand",
        label="Brand Studio",
        description=(
            "Identidad de marca completa: nombre, historia, posicionamiento (Brand Love Key),"
            " narrativa (StoryBrand), identidad visual, voz, equipo, testimonios, autoridad,"
            " assets de comunicación"
        ),
        route_prefix="brand-studio",
        model_class=_lazy_brand_settings(),
        repo_factory=_brand_repo_factory,
        read_fn=_brand_read_fn,
        keywords=("marca", "brand", "identidad", "posicionamiento", "narrativa"),
    )
