"""IEditionLandingClonePort — cross-module port for cloning landings per edition.

The **offer** module owns the edition aggregate and drives the clone
flow; the **landing** module owns the ``LandingPage`` aggregate and
knows how to copy/tokenize/regenerate its content. This port is the
explicit DDD contract between them.

The concrete adapter lives in
``landing.application.edition_clone_adapter.LandingEditionCloneAdapter``
and is wired at the API layer via :func:`create_edition_landing_clone_port`
— lazy import keeps the dependency direction inversion intact.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class LandingRef:
    """Opaque reference to a landing page returned by the clone port.

    Keeps the offer module from depending on the ``LandingPage``
    aggregate; callers that need the full object go through the landing
    module's own API.

    ``is_published`` is surfaced so the offer-studio UI can render a
    publish-state chip without a second round-trip to the landing module.
    """

    id: "UUID"
    slug: str
    is_published: bool = False


class IEditionLandingClonePort(ABC):
    """Cross-module port for cloning landings across editions.

    Implemented by the landing module (which owns the aggregate) and
    wired into :class:`EditionCloneService` via the factory below. The
    adapter MUST NOT commit the session — the orchestrating service
    owns the transaction boundary so the entire clone (edition +
    landing + assets) succeeds or rolls back atomically.
    """

    @abstractmethod
    def get_for_edition(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        edition_id: UUID | None,
    ) -> LandingRef | None:
        """Return the landing for ``(offer, edition)`` or ``None``.

        Passing ``edition_id=None`` looks up the offer-level template
        (``edition_id IS NULL``). Always tenant-scoped.
        """
        ...

    @abstractmethod
    def clone_to_edition(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        source_landing_id: UUID,
        target_edition_id: UUID,
        target_slug: str,
        strategy: str,
        substitutions: dict[str, str] | None = None,
        regeneration_context: dict[str, Any] | None = None,
    ) -> LandingRef:
        """Clone ``source_landing_id`` into a new row bound to ``target_edition_id``.

        ``strategy`` values:

        - ``"literal"`` — deep copy, no content changes.
        - ``"date_replace"`` — deep copy + tokenizer substitution using
          ``substitutions``.
        - ``"ai_regen"`` — deep copy + flag for async regeneration.

        The new row is created with ``is_published=False`` so an editor
        must review and publish explicitly.
        """
        ...


def create_edition_landing_clone_port(db: Session) -> IEditionLandingClonePort:
    """Instantiate the canonical adapter.

    Lazy-imports the concrete adapter so the static import graph stays
    clean (DDD architecture test scans top-level imports). Call this at
    the API composition root; pass the session the clone service uses
    so both participate in the same transaction.
    """
    from luana_core_landing.application.edition_clone_adapter import (
        LandingEditionCloneAdapter,
    )

    return LandingEditionCloneAdapter(db)


__all__ = [
    "IEditionLandingClonePort",
    "LandingRef",
    "create_edition_landing_clone_port",
]
