"""Tests for scripts/backfill_copilot_content_to_blocks.py.

TDD: these tests are written RED before the script implementation.

Test surfaces per CONTRACT §14.2:
  1. test_dry_run_does_not_mutate_db
  2. test_apply_converts_legacy_rows
  3. test_idempotent_rerun
  4. test_batch_size_respects_limit
  5. test_tenant_filter_isolation
  6. test_corrupt_message_skipped_with_audit
  7. test_audit_table_records_run
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_legacy_message(content: str = "Hello legacy", role: str = "user") -> dict:
    """v1 shape: no id, no blocks, just role + content."""
    return {"role": role, "content": content}


def _make_v2_message(content: str = "Hello v2") -> dict:
    """v2 shape: has id, blocks present."""
    return {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": content,
        "status": "sent",
        "created_at": "2026-04-29T00:00:00+00:00",
        "blocks": [
            {
                "type": "text",
                "id": str(uuid.uuid4()),
                "markdown": content,
            }
        ],
    }


def _make_corrupt_message() -> dict:
    """Message missing both role and content — codec will fail."""
    return {"no_role": True, "no_content": True}


def _insert_conv(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    messages: list[dict],
) -> uuid.UUID:
    """Insert a minimal copilot_conversations row and return its id."""
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    # Use CURRENT_TIMESTAMP for SQLite + PostgreSQL compat
    db.execute(
        text(
            """
            INSERT INTO copilot_conversations
                (id, tenant_id, user_id, messages, created_at, updated_at)
            VALUES
                (:id, :tenant_id, :user_id, :messages, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "id": str(conv_id),
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "messages": json.dumps(messages),
        },
    )
    db.commit()
    return conv_id


def _get_messages(db: Session, conv_id: uuid.UUID) -> list[dict]:
    """Read messages JSONB for a conversation."""
    row = db.execute(
        text("SELECT messages FROM copilot_conversations WHERE id = :id"),
        {"id": str(conv_id)},
    ).fetchone()
    if row is None:
        return []
    raw = row[0]
    if isinstance(raw, str):
        return json.loads(raw)
    return raw or []


def _get_audit_rows(db: Session, run_id: uuid.UUID) -> list[dict]:
    """Fetch rows from copilot_backfill_runs for a given run_id."""
    rows = db.execute(
        text("SELECT * FROM copilot_backfill_runs WHERE run_id = :run_id"),
        {"run_id": str(run_id)},
    ).fetchall()
    return [dict(r._mapping) for r in rows]


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> uuid.UUID:
    """A fixed tenant UUID for single-tenant tests."""
    return uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture()
def tenant_a() -> uuid.UUID:
    """Tenant A UUID for isolation tests."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture()
def tenant_b() -> uuid.UUID:
    """Tenant B UUID for isolation tests."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


# ── tests ─────────────────────────────────────────────────────────────────────


class TestDryRunDoesNotMutate:
    """CONTRACT test: dry-run must never write to DB."""

    def test_dry_run_does_not_mutate_db(self, db: Session, tenant_id: uuid.UUID) -> None:
        """Seed 5 legacy convs → run dry-run → assert no UPDATE was committed.

        Verifies: convs_updated = 0, DB rows unchanged.
        """
        conv_ids = []
        for i in range(5):
            cid = _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_legacy_message(f"legacy message {i}")],
            )
            conv_ids.append(cid)

        from scripts.backfill_copilot_content_to_blocks import run

        run_id = uuid.uuid4()
        stats = run(
            db=db,
            dry_run=True,
            tenant_id=tenant_id,
            batch_size=100,
            run_id=run_id,
            max_failure_rate=0.05,
        )

        assert stats.convs_updated == 0, "dry-run must not update any conv"

        # Confirm DB rows are still v1 shape
        for cid in conv_ids:
            msgs = _get_messages(db, cid)
            assert len(msgs) == 1
            # v1 shape: no "blocks" key in message
            assert "blocks" not in msgs[0], f"Conv {cid} was mutated by dry-run — blocks appeared in v1 row"


class TestApplyConvertsLegacyRows:
    """CONTRACT test: apply converts v1 messages to v2 with TextBlock."""

    def test_apply_converts_legacy_rows(self, db: Session, tenant_id: uuid.UUID) -> None:
        """Seed 5 convs with mix legacy/v2 messages → apply → assert:
        - blocks populated for legacy messages
        - content preserved (never nulled)
        - v2 messages untouched
        """
        legacy_content = "Mensaje legacy importante"
        v2_content = "Mensaje v2 ya listo"

        # 3 convs: all legacy
        legacy_ids = []
        for _ in range(3):
            cid = _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_legacy_message(legacy_content)],
            )
            legacy_ids.append(cid)

        # 2 convs: already v2
        v2_ids = []
        for _ in range(2):
            cid = _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_v2_message(v2_content)],
            )
            v2_ids.append(cid)

        from scripts.backfill_copilot_content_to_blocks import run

        run_id = uuid.uuid4()
        stats = run(
            db=db,
            dry_run=False,
            tenant_id=tenant_id,
            batch_size=100,
            run_id=run_id,
            max_failure_rate=0.05,
        )

        # Only legacy convs should have been updated
        assert stats.convs_updated == 3
        assert stats.convs_already_v2 == 2

        # Verify legacy convs now have blocks
        for cid in legacy_ids:
            msgs = _get_messages(db, cid)
            assert len(msgs) == 1
            msg = msgs[0]
            assert "blocks" in msg, f"Conv {cid}: blocks not present after apply"
            assert msg["blocks"] is not None and len(msg["blocks"]) > 0
            block = msg["blocks"][0]
            assert block["type"] == "text"
            assert block["markdown"] == legacy_content, (
                f"TextBlock markdown must match original content, got {block['markdown']}"
            )
            # Content must be preserved (invariant 2.2.1)
            assert msg.get("content") == legacy_content, "content must be preserved after backfill"

        # Verify v2 convs are untouched (same content still there)
        for cid in v2_ids:
            msgs = _get_messages(db, cid)
            assert msgs[0].get("content") == v2_content


class TestIdempotentRerun:
    """CONTRACT test: running apply twice → second run = 0 updates."""

    def test_idempotent_rerun(self, db: Session, tenant_id: uuid.UUID) -> None:
        """Apply 2x → second run reports convs_already_v2 = N, convs_updated = 0."""
        n = 5
        for i in range(n):
            _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_legacy_message(f"msg {i}")],
            )

        from scripts.backfill_copilot_content_to_blocks import run

        # First run
        stats1 = run(
            db=db,
            dry_run=False,
            tenant_id=tenant_id,
            batch_size=100,
            run_id=uuid.uuid4(),
            max_failure_rate=0.05,
        )
        assert stats1.convs_updated == n

        # Second run — must be a no-op
        stats2 = run(
            db=db,
            dry_run=False,
            tenant_id=tenant_id,
            batch_size=100,
            run_id=uuid.uuid4(),
            max_failure_rate=0.05,
        )
        assert stats2.convs_updated == 0, "Second apply run must update 0 convs (idempotent)"
        assert stats2.convs_already_v2 == n, (
            f"Expected {n} convs already v2 on second run, got {stats2.convs_already_v2}"
        )


class TestBatchSizeRespected:
    """CONTRACT test: --batch-size limits convs processed per batch."""

    def test_batch_size_respects_limit(self, db: Session, tenant_id: uuid.UUID) -> None:
        """Seed 25 convs + batch_size=10 → at least 3 batches, all convs processed."""
        total = 25
        for i in range(total):
            _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_legacy_message(f"batch msg {i}")],
            )

        batch_calls: list[int] = []

        from scripts import backfill_copilot_content_to_blocks as _script_mod

        original_run_batch = _script_mod._run_batch  # type: ignore[attr-defined]

        def _spy_run_batch(*args: Any, **kwargs: Any) -> Any:
            result = original_run_batch(*args, **kwargs)
            batch_calls.append(1)
            return result

        with patch.object(_script_mod, "_run_batch", side_effect=_spy_run_batch):
            stats = _script_mod.run(
                db=db,
                dry_run=False,
                tenant_id=tenant_id,
                batch_size=10,
                run_id=uuid.uuid4(),
                max_failure_rate=0.05,
            )

        assert stats.convs_updated == total, f"Expected {total} convs updated, got {stats.convs_updated}"
        assert len(batch_calls) >= 3, (
            f"Expected at least 3 batch calls for {total} convs / batch_size=10, got {len(batch_calls)}"
        )


class TestTenantFilterIsolation:
    """CONTRACT test: --tenant-id only processes that tenant's convs."""

    def test_tenant_filter_isolation(
        self,
        db: Session,
        tenant_a: uuid.UUID,
        tenant_b: uuid.UUID,
    ) -> None:
        """Seed legacy convs for tenant_a + tenant_b. Run with tenant_a filter →
        assert tenant_b convs UNTOUCHED, tenant_a converted.
        """
        a_ids = []
        for i in range(3):
            cid = _insert_conv(
                db,
                tenant_id=tenant_a,
                messages=[_make_legacy_message(f"tenant_a msg {i}")],
            )
            a_ids.append(cid)

        b_ids = []
        for i in range(3):
            cid = _insert_conv(
                db,
                tenant_id=tenant_b,
                messages=[_make_legacy_message(f"tenant_b msg {i}")],
            )
            b_ids.append(cid)

        from scripts.backfill_copilot_content_to_blocks import run

        stats = run(
            db=db,
            dry_run=False,
            tenant_id=tenant_a,
            batch_size=100,
            run_id=uuid.uuid4(),
            max_failure_rate=0.05,
        )

        assert stats.convs_updated == 3, f"Expected 3 tenant_a convs updated, got {stats.convs_updated}"

        # tenant_b convs must be untouched (still v1)
        for cid in b_ids:
            msgs = _get_messages(db, cid)
            assert "blocks" not in msgs[0], f"tenant_b conv {cid} was incorrectly mutated by tenant_a filter run"

        # tenant_a convs must be converted
        for cid in a_ids:
            msgs = _get_messages(db, cid)
            assert "blocks" in msgs[0]


class TestCorruptMessageSkipped:
    """CONTRACT test: corrupt messages are skipped with audit, other convs commit."""

    def test_corrupt_message_skipped_with_audit(self, db: Session, tenant_id: uuid.UUID) -> None:
        """Seed conv with corrupt message dict + 2 valid legacy convs →
        apply → assert:
        - corrupt conv in failed_conv_ids
        - convs_skipped_corrupt = 1
        - valid convs DO commit (per-conv try/except)
        """
        # Corrupt conv: message missing role and content
        corrupt_id = _insert_conv(
            db,
            tenant_id=tenant_id,
            messages=[_make_corrupt_message()],
        )

        # 2 valid legacy convs
        valid_ids = []
        for i in range(2):
            cid = _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_legacy_message(f"valid msg {i}")],
            )
            valid_ids.append(cid)

        from scripts.backfill_copilot_content_to_blocks import run

        run_id = uuid.uuid4()
        stats = run(
            db=db,
            dry_run=False,
            tenant_id=tenant_id,
            batch_size=100,
            run_id=run_id,
            max_failure_rate=1.0,  # don't abort on high failure rate for this test
        )

        # Valid convs should still commit despite one corrupt
        assert stats.convs_updated == 2, f"Expected 2 valid convs updated, got {stats.convs_updated}"
        assert stats.convs_skipped_corrupt == 1

        # Corrupt conv must appear in failed_conv_ids
        failed_strs = [str(fid) for fid in stats.failed_conv_ids]
        assert str(corrupt_id) in failed_strs, f"Corrupt conv {corrupt_id} not in failed_conv_ids: {failed_strs}"

        # Valid convs should have blocks
        for cid in valid_ids:
            msgs = _get_messages(db, cid)
            assert "blocks" in msgs[0], f"Valid conv {cid} missing blocks after apply"


class TestAuditTableRecordsRun:
    """CONTRACT test: apply writes audit row to copilot_backfill_runs."""

    def test_audit_table_records_run(self, db: Session, tenant_id: uuid.UUID) -> None:
        """Run --apply → assert copilot_backfill_runs row exists with:
        - status='completed', mode='apply'
        - run_id matches CLI flag (or auto-gen UUID)
        - convs_scanned + msgs_legacy_converted match counters
        """
        n = 3
        for i in range(n):
            _insert_conv(
                db,
                tenant_id=tenant_id,
                messages=[_make_legacy_message(f"audit msg {i}")],
            )

        from scripts.backfill_copilot_content_to_blocks import run

        run_id = uuid.uuid4()
        stats = run(
            db=db,
            dry_run=False,
            tenant_id=tenant_id,
            batch_size=100,
            run_id=run_id,
            max_failure_rate=0.05,
        )

        # Check audit row written
        audit_rows = _get_audit_rows(db, run_id)
        assert len(audit_rows) >= 1, f"Expected at least 1 audit row for run_id={run_id}, got {len(audit_rows)}"

        completed_rows = [r for r in audit_rows if r["status"] == "completed"]
        assert len(completed_rows) == 1, f"Expected exactly 1 'completed' audit row, got: {completed_rows}"

        row = completed_rows[0]
        assert row["mode"] == "apply"
        assert row["convs_scanned"] == stats.convs_scanned
        assert row["convs_updated"] == stats.convs_updated
        assert row["msgs_legacy_converted"] == stats.msgs_legacy_converted
        assert row["convs_skipped_corrupt"] == stats.convs_skipped_corrupt
