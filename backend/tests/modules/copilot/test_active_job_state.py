"""ActiveExtractionJob — dataclass roundtrip + merge preserves siblings.

Mirror of guided.state tests for the second sibling key stored in
``copilot_conversations.procedure_state`` JSONB.
"""

from __future__ import annotations

from src.modules.copilot.application.extraction.active_job_state import (
    ACTIVE_EXTRACTION_JOB_KEY,
    ActiveExtractionJob,
    load_active_job,
    merge_active_job,
)


class TestActiveExtractionJobRoundtrip:
    def test_to_json_roundtrip(self) -> None:
        job = ActiveExtractionJob(
            job_id="job-123",
            module="offer",
            entity_id="a96403b5-1111-2222-3333-444444444444",
            source_kind="url",
            source_ref="https://visionarias.lat/productos/foo",
            scope="full",
            mode="update",
            paused_at_block="identity",
            started_at="2026-04-23T21:34:14Z",
        )

        serialized = job.to_json()
        rebuilt = ActiveExtractionJob.from_json(serialized)

        assert rebuilt is not None
        assert rebuilt == job

    def test_from_json_none_returns_none(self) -> None:
        assert ActiveExtractionJob.from_json(None) is None

    def test_from_json_empty_dict_returns_none(self) -> None:
        assert ActiveExtractionJob.from_json({}) is None

    def test_from_json_missing_job_id_returns_none(self) -> None:
        assert (
            ActiveExtractionJob.from_json(
                {
                    "module": "brand",
                    "source_kind": "url",
                },
            )
            is None
        )

    def test_from_json_missing_module_returns_none(self) -> None:
        assert (
            ActiveExtractionJob.from_json(
                {
                    "job_id": "abc",
                    "source_kind": "url",
                },
            )
            is None
        )

    def test_from_json_coerces_types(self) -> None:
        rebuilt = ActiveExtractionJob.from_json(
            {
                "job_id": "job-1",
                "module": "brand",
                "entity_id": None,
                "source_kind": "doc",
                "source_ref": "asset-uuid",
                "scope": "section",
                "mode": "initial",
                "paused_at_block": None,
                "started_at": "2026-04-23T00:00:00Z",
            },
        )
        assert rebuilt is not None
        assert rebuilt.entity_id is None
        assert rebuilt.paused_at_block is None
        assert rebuilt.module == "brand"


class TestLoadActiveJob:
    def test_none_procedure_state_returns_none(self) -> None:
        assert load_active_job(None) is None

    def test_empty_procedure_state_returns_none(self) -> None:
        assert load_active_job({}) is None

    def test_procedure_state_without_key_returns_none(self) -> None:
        assert load_active_job({"guided": {"domain": "brand"}}) is None

    def test_loads_key_when_present(self) -> None:
        payload = {
            ACTIVE_EXTRACTION_JOB_KEY: {
                "job_id": "job-1",
                "module": "brand",
                "entity_id": None,
                "source_kind": "url",
                "source_ref": "https://example.com",
                "scope": "full",
                "mode": "initial",
                "paused_at_block": None,
                "started_at": "2026-04-23T00:00:00Z",
            },
        }
        loaded = load_active_job(payload)
        assert loaded is not None
        assert loaded.job_id == "job-1"
        assert loaded.module == "brand"

    def test_non_dict_procedure_state_returns_none(self) -> None:
        # Defensive: if storage layer returns a weird value we don't blow up.
        assert load_active_job("not a dict") is None  # type: ignore[arg-type]


class TestMergeActiveJob:
    def test_merge_adds_key_when_none_present(self) -> None:
        job = ActiveExtractionJob(
            job_id="j1",
            module="brand",
            entity_id=None,
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="2026-04-23T00:00:00Z",
        )
        result = merge_active_job(None, job)
        assert ACTIVE_EXTRACTION_JOB_KEY in result
        assert result[ACTIVE_EXTRACTION_JOB_KEY]["job_id"] == "j1"

    def test_merge_preserves_siblings(self) -> None:
        """The ``guided`` key must survive when we set/clear ``active_extraction_job``."""
        existing = {
            "guided": {
                "domain": "offer",
                "entity_id": "abc",
                "current_block_id": "identity",
                "completed_blocks": [],
                "started_at": "2026-04-23T21:30:00Z",
            },
        }
        job = ActiveExtractionJob(
            job_id="j2",
            module="offer",
            entity_id="abc",
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="update",
            paused_at_block="identity",
            started_at="2026-04-23T22:01:00Z",
        )
        result = merge_active_job(existing, job)
        assert "guided" in result
        assert result["guided"]["domain"] == "offer"
        assert ACTIVE_EXTRACTION_JOB_KEY in result

    def test_merge_clears_key_on_none(self) -> None:
        """Passing ``job=None`` removes the key but keeps siblings."""
        existing = {
            "guided": {
                "domain": "brand",
                "entity_id": None,
                "current_block_id": "identity",
                "completed_blocks": [],
                "started_at": "2026-04-23T00:00:00Z",
            },
            ACTIVE_EXTRACTION_JOB_KEY: {
                "job_id": "old",
                "module": "brand",
            },
        }
        result = merge_active_job(existing, None)
        assert ACTIVE_EXTRACTION_JOB_KEY not in result
        assert "guided" in result

    def test_merge_does_not_mutate_input(self) -> None:
        existing: dict = {"guided": {"domain": "brand"}}
        job = ActiveExtractionJob(
            job_id="j",
            module="brand",
            entity_id=None,
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="",
        )
        merge_active_job(existing, job)
        # Caller's dict untouched.
        assert ACTIVE_EXTRACTION_JOB_KEY not in existing
