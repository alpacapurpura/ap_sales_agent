"""Commercial calendar ``CopilotProvider`` — F1 shim."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luana_core_copilot.domain.ports import BaseCopilotProvider, ModuleData

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_commercial_calendar.infrastructure.repositories.calendar_event_repository import (
        CalendarEventRepository,
    )


def _calendar_repo_factory(db: object) -> object:
    from luana_core_commercial_calendar.infrastructure.repositories.calendar_event_repository import (
        CalendarEventRepository,
    )

    return CalendarEventRepository(db)


def _calendar_read_fn(repo: object, tenant_id: UUID) -> list:
    from luana_core_platform.domain.datetime_utils import utc_today

    today = utc_today()
    return cast("CalendarEventRepository", repo).list_events(
        country_code="PE",
        year=today.year,
        tenant_id=tenant_id,
    )


class CommercialCalendarCopilotProvider(BaseCopilotProvider):
    """Commercial calendar module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "commercial_calendar"

    @property
    def label(self) -> str:
        return "Calendario Comercial"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="commercial_calendar",
            label="Calendario Comercial",
            description=(
                "Eventos del calendario comercial: feriados nacionales, campanas,"
                " temporadas de venta, dias especiales. Eventos del sistema +"
                " eventos custom por tenant."
            ),
            route_prefix="commercial-calendar",
            model_class=None,
            repo_factory=_calendar_repo_factory,
            read_fn=_calendar_read_fn,
            keywords=(
                "calendario",
                "feriado",
                "campana",
                "temporada",
                "cyber",
                "holiday",
                "sale",
            ),
        )
