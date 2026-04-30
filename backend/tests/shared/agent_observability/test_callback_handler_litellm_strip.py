"""Tests for D-7 LiteLLM provider prefix strip in base_callback_handler.

Contract: S3 PR-2 D-7 — recorder stores bare model name (no provider prefix)
so existing Streamlit queries by model name remain compatible post-LiteLLM.

TDD RED-first per tdd-mandatory.md.
"""

from __future__ import annotations


def test_strips_provider_prefix() -> None:
    """'deepseek/deepseek-v4-flash' → recorder stores 'deepseek-v4-flash'."""
    from src.shared.agent_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={"kwargs": {"model_name": "deepseek/deepseek-v4-flash"}},
        metadata=None,
    )
    assert model == "deepseek-v4-flash"
    # Provider from serialized is unknown (not in metadata) — that's fine;
    # recorder also resolves provider from span context.
    assert provider == "unknown"


def test_strips_openai_prefix() -> None:
    """'openai/gpt-4o-mini' → recorder stores 'gpt-4o-mini'."""
    from src.shared.agent_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    _, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={"kwargs": {"model_name": "openai/gpt-4o-mini"}},
        metadata=None,
    )
    assert model == "gpt-4o-mini"


def test_bare_model_name_unchanged() -> None:
    """'gpt-4o-mini' (no slash) → stored as-is (backwards compat)."""
    from src.shared.agent_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    _, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={"kwargs": {"model_name": "gpt-4o-mini"}},
        metadata=None,
    )
    assert model == "gpt-4o-mini"


def test_metadata_ls_model_name_strip() -> None:
    """Strip also works when model comes from LangChain ls_model_name metadata."""
    from src.shared.agent_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    _, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={},
        metadata={"ls_provider": "deepseek", "ls_model_name": "deepseek/deepseek-v4-flash"},
    )
    assert model == "deepseek-v4-flash"
