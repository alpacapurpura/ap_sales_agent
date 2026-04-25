"""Fixtures for ``tests/quality/`` — golden runner + judge stub.

The default mode is ``stubbed``: the judge LLM is replaced by a stub that
returns 4.0 across all dimensions, proving the pipeline plumbs correctly
without burning OpenAI budget on every CI run.

Set ``RUN_LLM_JUDGE=1`` in the env to flip to a real NANO call (used by
the weekly cron + ad-hoc inspection). Threshold ≥3.5 still applies — the
real LLM may dip below for genuine regressions, which is exactly the
signal we want.
"""

from __future__ import annotations

import json
import os

import pytest
from langchain_core.messages import AIMessage


class _StubJudgeLLM:
    """Stub LLM that returns a fixed 4.0/dim payload — pipeline integration test."""

    def __init__(self, score: float = 4.0):
        self.score = score
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        payload = {
            "accuracy": {"score": self.score, "reason": "stub: ok"},
            "brand_coherence": {"score": self.score, "reason": "stub: ok"},
            "tone": {"score": self.score, "reason": "stub: ok"},
            "utility": {"score": self.score, "reason": "stub: ok"},
        }
        return AIMessage(
            content=json.dumps(payload),
            response_metadata={"id": "stub_resp"},
        )


@pytest.fixture
def judge_llm():
    """Default to stubbed; opt-in real NANO via ``RUN_LLM_JUDGE=1``."""
    if os.getenv("RUN_LLM_JUDGE") == "1":
        # Real NANO path — defer import to avoid pulling LLMFactory in stub mode.
        from src.core.enums import ModelRole
        from src.shared.infrastructure.llm.factory import LLMFactory

        return LLMFactory.get_service().get_client(ModelRole.NANO)
    return _StubJudgeLLM(score=4.0)
