"""Tests for D-7 LiteLLM provider prefix handling in base_callback_handler.

⚠️  T-1 (PI-12 S1 sales-agent-litellm-canonicalization, A1 ratificada):
the legacy D-7 strip behavior is **REVERSED**. The recorder now stores the
model field SLASHED (canonical LiteLLM format, e.g.
``"deepseek/deepseek-v4-flash"``). Provider is derived via
:func:`litellm.get_llm_provider` (position 1 of the 4-tuple) — see
:meth:`BaseAgentCallbackHandler._canonical_provider`.

Rationale: future-proof for multi-namespace providers
(``bedrock/anthropic.claude-v3``, ``vertex_ai/gemini-1.5-pro``) where the
model identity itself contains the provider taxonomy. Streamlit queries
that filter by bare model name must update to filter by the slashed
canonical form (covered in T-9 documentation purge).

This file's purpose flipped from "guard the strip" to "guard the
preservation" — invoking the same helper, asserting the inverse outcome.

TDD RED-first per `.claude/rules/tdd-mandatory.md`.
"""

from __future__ import annotations


def test_preserves_deepseek_provider_prefix() -> None:
    """A1 — 'deepseek/deepseek-v4-flash' stored as-is (slashed)."""
    from luana_core_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={"kwargs": {"model_name": "deepseek/deepseek-v4-flash"}},
        metadata=None,
    )
    assert model == "deepseek/deepseek-v4-flash"
    # Provider derived via litellm.get_llm_provider — canonical 'deepseek',
    # NOT the legacy 'unknown' fallback when metadata.ls_provider was missing.
    assert provider == "deepseek"


def test_preserves_openai_provider_prefix() -> None:
    """A1 — 'openai/gpt-4o-mini' stored as-is (slashed)."""
    from luana_core_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={"kwargs": {"model_name": "openai/gpt-4o-mini"}},
        metadata=None,
    )
    assert model == "openai/gpt-4o-mini"
    assert provider == "openai"


def test_bare_model_name_unchanged() -> None:
    """Model without slash — preserved as-is, provider falls back via SDK."""
    from luana_core_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    _, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={"kwargs": {"model_name": "gpt-4o-mini"}},
        metadata=None,
    )
    # Bare name preserved; the SDK still resolves provider via its model registry.
    assert model == "gpt-4o-mini"


def test_metadata_ls_model_name_preserved_slashed() -> None:
    """Slashed model from LangChain ls_model_name metadata is preserved."""
    from luana_core_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
        serialized={},
        metadata={"ls_provider": "deepseek", "ls_model_name": "deepseek/deepseek-v4-flash"},
    )
    assert model == "deepseek/deepseek-v4-flash"
    assert provider == "deepseek"
