"""Arch test: ExtractionJob enum names are registered as ARQ workers.

If a worker function is renamed (``run_brand_extraction`` → ``brand_extract_job``),
the enqueue call sites tied to the enum immediately fail at dispatch time with
a clear error. This test makes the mismatch fail at CI instead of in prod.
"""

from __future__ import annotations

from src.shared.domain.extraction_jobs import ExtractionJob
from src.workers.settings import WorkerSettings


def test_every_extraction_job_enum_is_registered_worker_function() -> None:
    """Every ExtractionJob value MUST name a function in WorkerSettings.functions."""
    registered_names = {fn.__name__ for fn in WorkerSettings.functions}
    missing = [job.value for job in ExtractionJob if job.value not in registered_names]
    assert not missing, (
        f"ExtractionJob values missing from WorkerSettings.functions: {missing}. "
        "Either add the worker function to WorkerSettings.functions or remove "
        "the enum entry."
    )
