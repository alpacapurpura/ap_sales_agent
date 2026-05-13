"""Fixtures for ``tests/quality/sales_agent_goldens/`` — golden runner stub.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Default mode = ``stubbed``: the judge LLM is replaced by a stub that returns
4.0 across the 5 sales dimensions, proving the pipeline plumbs correctly
without burning OpenAI/Anthropic budget on every CI run.

Set ``RUN_LLM_JUDGE=1`` in the env to flip to a real NANO call (used by the
weekly cron + ad-hoc inspection). Threshold ≥3.5 still applies — the real
LLM may dip below for genuine regressions, which is the signal we want.
"""

from __future__ import annotations

import json
import os

import pytest
from langchain_core.messages import AIMessage


class _StubSalesJudgeLLM:
    """Stub LLM returning fixed 4.0/dim payload — pipeline integration test."""

    def __init__(self, score: float = 4.0):
        self.score = score
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        payload = {
            "brand_voice_fidelity": {"score": self.score, "reason": "stub: ok"},
            "channel_format_correctness": {"score": self.score, "reason": "stub: ok"},
            "commercial_effectiveness": {"score": self.score, "reason": "stub: ok"},
            "pii_safety": {"score": self.score, "reason": "stub: ok"},
            "tone_locale_fitness": {"score": self.score, "reason": "stub: ok"},
        }
        return AIMessage(
            content=json.dumps(payload),
            response_metadata={"id": "stub_resp_sales"},
        )


@pytest.fixture
def sales_judge_llm():
    """Default to stubbed; opt-in real NANO via ``RUN_LLM_JUDGE=1``."""
    if os.getenv("RUN_LLM_JUDGE") == "1":
        from luana_core_platform.core.enums import ModelRole
        from luana_core_llm.factory import LLMFactory

        return LLMFactory.get_service().get_client(ModelRole.NANO)
    return _StubSalesJudgeLLM(score=4.0)
