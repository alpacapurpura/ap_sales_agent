"""ARQ extraction job names — single source of truth.

Hardcoded strings like ``"run_brand_extraction"`` used to live in 6 places
(tool dispatch, REST endpoints, worker registration, tests). A rename of any
worker was a silent break. This enum collapses them into one reference so the
ARQ ``enqueue_job`` call sites and the ``WorkerSettings.functions`` list share
a name — if they drift, the worker startup fails loud.
"""

from __future__ import annotations

from enum import StrEnum


class ExtractionJob(StrEnum):
    """Canonical ARQ job names for extraction workers."""

    BRAND = "run_brand_extraction"
    OFFER = "run_offer_extraction"


__all__ = ["ExtractionJob"]
