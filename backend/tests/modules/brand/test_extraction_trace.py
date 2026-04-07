"""Tests for ExtractionTraceCollector -- event accumulation and DB persistence."""

import uuid
from unittest.mock import MagicMock

from src.modules.brand.application.extraction_trace import ExtractionTraceCollector


class TestExtractionTraceCollector:
    def _make_collector(self, db=None):
        return ExtractionTraceCollector(
            db=db or MagicMock(),
            tenant_id=uuid.uuid4(),
            job_id="test-job-123",
            mode="initial",
            profile_name="safe",
            url="https://example.com",
        )

    def test_events_accumulate(self):
        tc = self._make_collector()
        tc.crawl_start("https://example.com")
        tc.crawl_end(1.5, content_len=5000)
        tc.wave_start(1, ["identity", "story"])
        tc.section_start("identity", prompt_length=1000)
        tc.section_success("identity", 2.0, field_count=5, fields=["brand_name"])

        assert len(tc._events) == 5
        assert tc._events[0]["event"] == "crawl_start"
        assert tc._events[4]["event"] == "section_success"

    def test_section_failure_recorded(self):
        tc = self._make_collector()
        tc.section_failed("story", 3.0, error="Timeout", error_type="TimeoutError")

        assert len(tc._events) == 1
        assert tc._events[0]["event"] == "section_failed"
        assert tc._events[0]["meta"]["error"] == "Timeout"

    def test_section_timeout_recorded(self):
        tc = self._make_collector()
        tc.section_timeout("visuals", 120.0, timeout_limit=120.0)

        assert tc._events[0]["event"] == "section_timeout"

    def test_finish_persists_to_db(self):
        mock_db = MagicMock()
        tc = self._make_collector(db=mock_db)
        tc.set_content_length(10000)
        tc.set_sections_total(6)
        tc.crawl_start("https://example.com")

        trace_id = tc.finish(status="completed", sections_succeeded=5)

        assert trace_id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        row = mock_db.add.call_args[0][0]
        assert row.status == "completed"
        assert row.sections_succeeded == 5
        assert row.content_length == 10000

    def test_set_content_length(self):
        tc = self._make_collector()
        tc.set_content_length(5000)
        assert tc._content_length == 5000

    def test_merge_events(self):
        tc = self._make_collector()
        tc.merge_start()
        tc.merge_end(0.5)
        assert tc._events[0]["event"] == "merge_start"
        assert tc._events[1]["event"] == "merge_end"

    def test_wave_pause_recorded(self):
        tc = self._make_collector()
        tc.wave_pause(1, 5.0)
        assert tc._events[0]["event"] == "wave_pause"
        assert tc._events[0]["meta"]["delay_s"] == 5.0

    def test_set_sections_total(self):
        tc = self._make_collector()
        tc.set_sections_total(8)
        assert tc._sections_total == 8

    def test_finish_returns_uuid(self):
        mock_db = MagicMock()
        tc = self._make_collector(db=mock_db)
        trace_id = tc.finish(status="failed", error_message="Something broke")

        assert isinstance(trace_id, uuid.UUID)
        row = mock_db.add.call_args[0][0]
        assert row.status == "failed"
        assert row.error_message == "Something broke"

    def test_finish_calculates_duration(self):
        mock_db = MagicMock()
        tc = self._make_collector(db=mock_db)
        tc.finish(status="completed", sections_succeeded=0)

        row = mock_db.add.call_args[0][0]
        assert row.total_duration_s >= 0
        assert isinstance(row.total_duration_s, float)

    def test_events_contain_timestamps(self):
        tc = self._make_collector()
        tc.crawl_start("https://example.com")
        assert "ts" in tc._events[0]

    def test_include_visuals_and_assets_flags(self):
        mock_db = MagicMock()
        tc = ExtractionTraceCollector(
            db=mock_db,
            tenant_id=uuid.uuid4(),
            job_id="test-job-456",
            mode="update",
            profile_name="fast",
            url="https://example.com",
            include_visuals=True,
            include_assets=True,
        )
        tc.finish(status="completed", sections_succeeded=0)

        row = mock_db.add.call_args[0][0]
        assert row.include_visuals == "true"
        assert row.include_assets == "true"
        assert row.mode == "update"
        assert row.profile_name == "fast"
