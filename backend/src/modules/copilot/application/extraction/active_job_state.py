"""Active extraction job state — persisted inside ``conversation.procedure_state``.

Mirror of ``guided.state`` for the second sibling key we now track:
``active_extraction_job``. One conversation can hold both keys at the same
time (guided run paused while a URL is being scraped).

Lightweight dataclass + JSON (de)serialisation. No ORM, no migration — the
state lives inside a JSONB column we already own.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ACTIVE_EXTRACTION_JOB_KEY = "active_extraction_job"


@dataclass(slots=True)
class ActiveExtractionJob:
    """Snapshot of the in-flight extraction job for a copilot conversation.

    Fields follow the contract in
    ``docs/mejoras-proceso/copilot-extraction-unified-design.md`` § "State contract".
    """

    job_id: str
    module: str  # "brand" | "offer" (buyer_persona/asset not yet wired)
    entity_id: str | None
    source_kind: str  # "url" | "doc"
    source_ref: str  # URL or asset_id
    scope: str  # "full" | "section" | "field" | "visuals"
    mode: str  # "initial" | "update" | "suggest"
    paused_at_block: str | None
    started_at: str

    @classmethod
    def from_json(cls, data: dict[str, Any] | None) -> ActiveExtractionJob | None:
        """Return an ``ActiveExtractionJob`` from a JSON dict, or ``None`` if malformed."""
        if not data or not isinstance(data, dict):
            return None
        job_id = data.get("job_id")
        module = data.get("module")
        if not job_id or not module:
            return None
        entity_id_raw = data.get("entity_id")
        paused_raw = data.get("paused_at_block")
        return cls(
            job_id=str(job_id),
            module=str(module),
            entity_id=(str(entity_id_raw) if entity_id_raw else None),
            source_kind=str(data.get("source_kind", "")),
            source_ref=str(data.get("source_ref", "")),
            scope=str(data.get("scope", "")),
            mode=str(data.get("mode", "")),
            paused_at_block=(str(paused_raw) if paused_raw else None),
            started_at=str(data.get("started_at", "")),
        )

    def to_json(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "job_id": self.job_id,
            "module": self.module,
            "entity_id": self.entity_id,
            "source_kind": self.source_kind,
            "source_ref": self.source_ref,
            "scope": self.scope,
            "mode": self.mode,
            "paused_at_block": self.paused_at_block,
            "started_at": self.started_at,
        }


def load_active_job(
    procedure_state: dict[str, Any] | None,
) -> ActiveExtractionJob | None:
    """Extract the active job from the raw ``procedure_state`` JSONB payload."""
    if not procedure_state or not isinstance(procedure_state, dict):
        return None
    return ActiveExtractionJob.from_json(procedure_state.get(ACTIVE_EXTRACTION_JOB_KEY))


def merge_active_job(
    procedure_state: dict[str, Any] | None,
    job: ActiveExtractionJob | None,
) -> dict[str, Any]:
    """Return a new ``procedure_state`` dict with ``active_extraction_job`` set or removed.

    Preserves any sibling keys (e.g. ``guided``) so the two subsystems can
    coexist — a guided run can be paused while an extraction is mid-flight.
    """
    current = dict(procedure_state) if procedure_state else {}
    if job is None:
        current.pop(ACTIVE_EXTRACTION_JOB_KEY, None)
    else:
        current[ACTIVE_EXTRACTION_JOB_KEY] = job.to_json()
    return current


__all__ = [
    "ACTIVE_EXTRACTION_JOB_KEY",
    "ActiveExtractionJob",
    "load_active_job",
    "merge_active_job",
]
