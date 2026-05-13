"""Tests for GET /conversations/{id}/active-jobs endpoint (Fase 5 / Bug 3).

Verifies:
- 200 + empty jobs when no active extraction job stored
- 200 + job data when active job exists in procedure_state
- 404 when conversation not found or not owned by user
- poll_endpoint has the correct format per module
- Redis data is merged into the response when available
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
USER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
CONVERSATION_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
OFFER_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())


def _make_conv_mock(
    conv_id: uuid.UUID = CONVERSATION_ID,
    procedure_state: dict | None = None,
) -> MagicMock:
    """Build a minimal CopilotConversationModel mock."""
    m = MagicMock()
    m.id = conv_id
    m.tenant_id = TENANT_ID
    m.procedure_state = procedure_state
    m.title = "Test conv"
    m.title_auto_generated = False
    m.updated_at = MagicMock()
    m.message_count = 0
    m.total_tokens = 0
    m.last_tier_used = None
    m.archived_at = None
    m.messages = []
    return m


def _make_user_mock() -> MagicMock:
    m = MagicMock()
    m.id = USER_ID
    m.tenant_id = TENANT_ID
    return m


class TestActiveJobsEndpointHappyPath:
    """GET /conversations/{id}/active-jobs — happy path scenarios."""

    async def test_returns_empty_jobs_when_no_active_job(self) -> None:
        """Returns 200 with jobs=[] when conversation has no active_extraction_job."""
        from luana_core_copilot.api.conversations import get_active_jobs

        conv_mock = _make_conv_mock(procedure_state={})
        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = conv_mock
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            patch(
                "luana_core_copilot.application.extraction.active_job_persistence.read_active_job",
                return_value=None,
            ),
        ):
            result = await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        assert result.jobs == []

    async def test_returns_job_when_active_job_exists(self) -> None:
        """Returns 200 with job data when procedure_state has active_extraction_job."""
        from luana_core_copilot.api.conversations import get_active_jobs
        from luana_core_copilot.application.extraction.active_job_state import (
            ActiveExtractionJob,
        )

        active_job = ActiveExtractionJob(
            job_id=JOB_ID,
            module="offer",
            entity_id=OFFER_ID,
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="2026-04-24T12:00:00+00:00",
        )
        conv_mock = _make_conv_mock()
        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = conv_mock
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            patch(
                "luana_core_copilot.api.conversations.read_active_job",
                return_value=active_job,
            ),
            patch("luana_core_platform.core.database.redis_client", None),
        ):
            result = await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        assert len(result.jobs) == 1
        job = result.jobs[0]
        assert job.job_id == JOB_ID
        assert job.module == "offer"
        assert job.entity_id == OFFER_ID
        assert job.source_ref == "https://example.com"

    async def test_poll_endpoint_format_offer(self) -> None:
        """poll_endpoint for 'offer' module uses extract-full-offer/status pattern."""
        from luana_core_copilot.api.conversations import get_active_jobs
        from luana_core_copilot.application.extraction.active_job_state import (
            ActiveExtractionJob,
        )

        active_job = ActiveExtractionJob(
            job_id=JOB_ID,
            module="offer",
            entity_id=OFFER_ID,
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="2026-04-24T12:00:00+00:00",
        )
        conv_mock = _make_conv_mock()
        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = conv_mock
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            patch(
                "luana_core_copilot.api.conversations.read_active_job",
                return_value=active_job,
            ),
            patch("luana_core_platform.core.database.redis_client", None),
        ):
            result = await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        poll = result.jobs[0].poll_endpoint
        assert "extract-full-offer" in poll
        assert JOB_ID in poll

    async def test_poll_endpoint_format_brand(self) -> None:
        """poll_endpoint for 'brand' module uses extract-full-brand/status pattern."""
        from luana_core_copilot.api.conversations import get_active_jobs
        from luana_core_copilot.application.extraction.active_job_state import (
            ActiveExtractionJob,
        )

        brand_job_id = str(uuid.uuid4())
        active_job = ActiveExtractionJob(
            job_id=brand_job_id,
            module="brand",
            entity_id=None,
            source_kind="url",
            source_ref="https://brand.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="2026-04-24T12:00:00+00:00",
        )
        conv_mock = _make_conv_mock()
        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = conv_mock
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            patch(
                "luana_core_copilot.api.conversations.read_active_job",
                return_value=active_job,
            ),
            patch("luana_core_platform.core.database.redis_client", None),
        ):
            result = await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        poll = result.jobs[0].poll_endpoint
        assert "extract-full-brand" in poll
        assert brand_job_id in poll

    async def test_redis_data_merged_when_available(self) -> None:
        """When Redis has progress data, it is merged into the DTO."""
        import json

        from luana_core_copilot.api.conversations import get_active_jobs
        from luana_core_copilot.application.extraction.active_job_state import (
            ActiveExtractionJob,
        )

        active_job = ActiveExtractionJob(
            job_id=JOB_ID,
            module="offer",
            entity_id=OFFER_ID,
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="2026-04-24T12:00:00+00:00",
        )

        redis_payload = {
            "status": "processing",
            "progress": 55,
            "stage": "Analizando secciones...",
            "filled_fields": ["headline_promise", "value_level"],
            "filled_fields_by_section": {"identity": ["headline_promise"], "strategy": ["value_level"]},
            "sections_touched": ["identity", "strategy"],
            "sections_completed": ["identity"],
            "finished_at": None,
        }
        redis_mock = MagicMock()
        redis_mock.get.return_value = json.dumps(redis_payload).encode()

        conv_mock = _make_conv_mock()
        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = conv_mock
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            patch(
                "luana_core_copilot.api.conversations.read_active_job",
                return_value=active_job,
            ),
            patch("luana_core_platform.core.database.redis_client", redis_mock),
        ):
            result = await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        job = result.jobs[0]
        assert job.status == "processing"
        assert job.progress == 55
        assert job.stage == "Analizando secciones..."
        assert "headline_promise" in job.filled_fields
        assert "identity" in job.sections_completed
        assert job.finished_at is None

    async def test_null_redis_values_when_redis_unavailable(self) -> None:
        """When Redis has no key (expired), status/progress/stage are None."""
        from luana_core_copilot.api.conversations import get_active_jobs
        from luana_core_copilot.application.extraction.active_job_state import (
            ActiveExtractionJob,
        )

        active_job = ActiveExtractionJob(
            job_id=JOB_ID,
            module="offer",
            entity_id=OFFER_ID,
            source_kind="url",
            source_ref="https://example.com",
            scope="full",
            mode="initial",
            paused_at_block=None,
            started_at="2026-04-24T12:00:00+00:00",
        )

        redis_mock = MagicMock()
        redis_mock.get.return_value = None  # key not found / expired

        conv_mock = _make_conv_mock()
        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = conv_mock
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            patch(
                "luana_core_copilot.api.conversations.read_active_job",
                return_value=active_job,
            ),
            patch("luana_core_platform.core.database.redis_client", redis_mock),
        ):
            result = await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        job = result.jobs[0]
        assert job.status is None
        assert job.progress is None
        assert job.stage is None
        assert job.filled_fields == []
        assert job.sections_completed == []


class TestActiveJobsEndpointError:
    """GET /conversations/{id}/active-jobs — error scenarios."""

    async def test_returns_404_when_conversation_not_found(self) -> None:
        """Returns 404 when the conversation doesn't exist or isn't owned by user."""
        from fastapi import HTTPException

        from luana_core_copilot.api.conversations import get_active_jobs

        repo_mock = MagicMock()
        repo_mock.get_by_id.return_value = None  # Not found
        user_mock = _make_user_mock()

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
                return_value=repo_mock,
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=TENANT_ID,
                db=MagicMock(),
            )

        assert exc_info.value.status_code == 404

    async def test_returns_401_when_no_tenant(self) -> None:
        """Returns 401 when tenant_id is None."""
        from fastapi import HTTPException

        from luana_core_copilot.api.conversations import get_active_jobs

        user_mock = _make_user_mock()

        with pytest.raises(HTTPException) as exc_info:
            await get_active_jobs(
                conversation_id=CONVERSATION_ID,
                current_user=user_mock,
                tenant_id=None,
                db=MagicMock(),
            )

        assert exc_info.value.status_code == 401
