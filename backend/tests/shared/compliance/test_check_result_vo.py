"""Tests for CheckResult value object — compliance domain layer."""

from __future__ import annotations

import pytest

from src.shared.compliance.domain.check_result import CheckResult


class TestCheckResultInvariants:
    def test_allowed_pass(self) -> None:
        r = CheckResult(allowed=True)
        assert r.allowed is True
        assert r.failed_policy is None
        assert r.reason is None
        assert r.evidence == {}

    def test_blocked_with_evidence(self) -> None:
        r = CheckResult(
            allowed=False,
            failed_policy="waba_24h",
            reason="No inbound in 24h window",
            evidence={"last_inbound_at": "2026-04-28T10:00:00Z", "hours_since_inbound": 26},
        )
        assert r.allowed is False
        assert r.failed_policy == "waba_24h"
        assert r.evidence["hours_since_inbound"] == 26

    def test_evidence_default_empty_dict(self) -> None:
        r = CheckResult(allowed=True)
        assert isinstance(r.evidence, dict)
        assert len(r.evidence) == 0

    def test_frozen(self) -> None:
        r = CheckResult(allowed=True)
        with pytest.raises((TypeError, AttributeError)):
            r.allowed = False  # type: ignore[misc]
