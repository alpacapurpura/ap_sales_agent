"""Lightweight trace collector for offer extraction jobs.

Captures timestamped events during extraction and persists them
to the offer_extraction_traces table when the job finishes.
Port of brand/application/extraction_trace.py for the offer module.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from luana_core_offer_studio.infrastructure.models.offer_extraction_trace_model import (
    OfferExtractionTrace,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class OfferExtractionTraceCollector:
    """Accumulates events in memory; flushes once to DB on finish()."""

    def __init__(
        self,
        db: Session,
        tenant_id: UUID,
        job_id: str,
        *,
        mode: str = "initial",
        url: str | None = None,
    ) -> None:
        """Initialize offer extraction trace collector."""
        self._db = db
        self._trace_id = uuid4()
        self._tenant_id = tenant_id
        self._job_id = job_id
        self._mode = mode
        self._url = url

        self._events: list[dict[str, Any]] = []
        self._t0 = time.monotonic()
        self._content_length = 0
        self._sections_total = 0

    # ------------------------------------------------------------------
    # Event recording
    # ------------------------------------------------------------------

    def _append(
        self,
        event: str,
        *,
        section: str | None = None,
        duration_s: float | None = None,
        **meta: Any,  # noqa: ANN401
    ) -> None:
        entry: dict[str, Any] = {
            "event": event,
            "ts": datetime.now(UTC).isoformat(),
        }
        if section:
            entry["section"] = section
        if duration_s is not None:
            entry["duration_s"] = round(duration_s, 3)
        if meta:
            entry["meta"] = {k: v for k, v in meta.items() if v is not None}
        self._events.append(entry)

    def set_content_length(self, length: int) -> None:
        """Set content length."""
        self._content_length = length

    def set_sections_total(self, total: int) -> None:
        """Set sections total."""
        self._sections_total = total

    def crawl_start(self, url: str) -> None:
        """Record crawl start."""
        self._append("crawl_start", url=url)

    def crawl_end(
        self,
        duration_s: float,
        *,
        content_len: int = 0,
    ) -> None:
        """Record crawl end."""
        self._append(
            "crawl_end",
            duration_s=duration_s,
            content_len=content_len,
        )

    def wave_start(self, wave: int, sections: list[str]) -> None:
        """Record wave start."""
        self._append("wave_start", wave=wave, sections=sections)

    def wave_pause(self, wave: int, delay_s: float) -> None:
        """Record wave pause."""
        self._append("wave_pause", wave=wave, delay_s=delay_s)

    def section_start(self, section: str, *, prompt_length: int = 0) -> None:
        """Record section start."""
        self._append("section_start", section=section, prompt_length=prompt_length)

    def section_success(
        self,
        section: str,
        duration_s: float,
        *,
        field_count: int = 0,
        fields: list[str] | None = None,
    ) -> None:
        """Record section success."""
        self._append(
            "section_success",
            section=section,
            duration_s=duration_s,
            field_count=field_count,
            fields=fields,
        )

    def section_failed(
        self,
        section: str,
        duration_s: float,
        *,
        error: str = "",
        error_type: str = "",
    ) -> None:
        """Record section failure."""
        self._append(
            "section_failed",
            section=section,
            duration_s=duration_s,
            error=error,
            error_type=error_type,
        )

    def merge_start(self) -> None:
        """Record merge start."""
        self._append("merge_start")

    def merge_end(self, duration_s: float) -> None:
        """Record merge end."""
        self._append("merge_end", duration_s=duration_s)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def finish(
        self,
        *,
        status: str = "completed",
        sections_succeeded: int = 0,
        error_message: str | None = None,
    ) -> UUID:
        """Flush the trace to the database. Returns the trace ID."""
        total_duration = round(time.monotonic() - self._t0, 3)

        row = OfferExtractionTrace(
            id=self._trace_id,
            tenant_id=self._tenant_id,
            job_id=self._job_id,
            mode=self._mode,
            url=self._url,
            status=status,
            content_length=self._content_length,
            sections_total=self._sections_total,
            sections_succeeded=sections_succeeded,
            total_duration_s=total_duration,
            error_message=error_message,
            events=self._events,
        )
        self._db.add(row)
        self._db.commit()
        return self._trace_id
