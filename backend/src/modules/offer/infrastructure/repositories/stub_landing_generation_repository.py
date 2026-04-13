"""Stub implementation of ``ILandingGenerationRepository``.

The real adapter will live in the ``landing`` module and persist the
generation job state. For Chunk 4a we only need the offer header
endpoints to be reachable — the stub returns ``None`` (no landing yet)
and echoes the generation request back so ``POST /generate`` succeeds
without persisting anything.

This unblocks the frontend on the header redesign while the landing
generation pipeline is still being built.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.modules.offer.application.ports import ILandingGenerationRepository


@dataclass
class _StubLanding:
    """Minimal stand-in landing object for the stub repository."""

    id: UUID
    tenant_id: UUID
    offer_id: UUID
    generated_at: None = None
    is_published: bool = False
    offer_snapshot_version: str | None = None
    generation_job_id: UUID | None = None
    generation_job_status: str = "queued"


class StubLandingGenerationRepository(ILandingGenerationRepository):
    """No-op repository that makes the header endpoints reachable.

    Every read returns ``None`` (no landing for any offer); every write
    returns an in-memory ``_StubLanding`` so the service layer can echo
    job metadata back to the caller. Swap for a real adapter once the
    landing generation pipeline lands.
    """

    def get_by_offer_id(self, tenant_id: UUID, offer_id: UUID) -> object | None:
        """Retrieve by offer id."""
        _ = (tenant_id, offer_id)
        return None

    def upsert_for_generation(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        snapshot_version: str,
        job_id: UUID,
        job_status: str,
    ) -> object:
        """Upsert for generation."""
        return _StubLanding(
            id=offer_id,
            tenant_id=tenant_id,
            offer_id=offer_id,
            offer_snapshot_version=snapshot_version,
            generation_job_id=job_id,
            generation_job_status=job_status,
        )

    def save(self, landing: object) -> object:
        """Save."""
        return landing


__all__ = ["StubLandingGenerationRepository"]
