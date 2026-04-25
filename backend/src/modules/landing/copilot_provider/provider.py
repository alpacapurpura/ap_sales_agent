"""Landing ``CopilotProvider`` — F1 shim."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from src.modules.copilot.domain.ports import BaseCopilotProvider, ModuleData

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.landing.infrastructure.repositories.landing_repository import (
        LandingRepository,
    )


def _landing_repo_factory(db: object) -> object:
    from src.modules.landing.infrastructure.repositories.landing_repository import (
        LandingRepository,
    )

    return LandingRepository(db)


def _landing_read_fn(repo: object, tenant_id: UUID) -> list:
    return cast("LandingRepository", repo).list_by_tenant(tenant_id)


class LandingCopilotProvider(BaseCopilotProvider):
    """Landing pages module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "landing"

    @property
    def label(self) -> str:
        return "Landing Pages"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="landing",
            label="Landing Pages",
            description=("Páginas de aterrizaje: generadas automáticamente o personalizadas, vinculadas a ofertas"),
            route_prefix="landing",
            model_class=None,
            repo_factory=_landing_repo_factory,
            read_fn=_landing_read_fn,
            keywords=("landing", "página", "aterrizaje"),
        )
