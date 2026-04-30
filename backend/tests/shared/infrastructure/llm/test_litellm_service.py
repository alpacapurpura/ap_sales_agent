"""Unit tests for LiteLLMService adapter.

TDD RED-first — tests written before implementation per tdd-mandatory.md.

Contract: §16 of S3 PR-2 CONTRACT.md.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.enums import ModelRole


@pytest.fixture()
def _settings_deepseek_nano(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch settings so NANO role maps to deepseek provider + deepseek-v4-flash model."""
    from src.core.enums import AIProvider

    monkeypatch.setattr("src.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")
    monkeypatch.setattr("src.core.config.settings.LITELLM_MASTER_KEY", "sk-test-master")
    monkeypatch.setattr("src.core.config.settings.AI_MODEL_NANO", "deepseek-v4-flash")
    monkeypatch.setattr("src.core.config.settings.AI_PROVIDER_NANO", AIProvider.DEEPSEEK)


def test_litellm_service_builds_model_alias_provider_slash_model(
    _settings_deepseek_nano: None,
) -> None:
    """LiteLLMService._litellm_model_name(NANO) returns 'deepseek/deepseek-v4-flash'."""
    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    alias = svc._litellm_model_name(ModelRole.NANO)
    assert alias == "deepseek/deepseek-v4-flash"


def test_litellm_service_get_client_targets_litellm_base_url(
    _settings_deepseek_nano: None,
) -> None:
    """get_client returns a ChatOpenAI instance pointing at LITELLM_BASE_URL."""
    from langchain_openai import ChatOpenAI

    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    client = svc.get_client(ModelRole.NANO)
    # ChatOpenAI stores base_url as openai_api_base or base_url depending on version
    base = getattr(client, "openai_api_base", None) or getattr(client, "base_url", None)
    assert base == "http://litellm:4000/v1"
    assert isinstance(client, ChatOpenAI)


def test_litellm_service_caches_per_model_temperature(
    _settings_deepseek_nano: None,
) -> None:
    """get_client(NANO, temperature=0.5) cached separately from temperature=0.7."""
    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    client_a = svc.get_client(ModelRole.NANO, temperature=0.5)
    client_b = svc.get_client(ModelRole.NANO, temperature=0.7)
    client_a2 = svc.get_client(ModelRole.NANO, temperature=0.5)

    # Different temperature → different instance
    assert client_a is not client_b
    # Same call → same cached instance
    assert client_a is client_a2


def test_litellm_service_get_embedding_model_targets_litellm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_embedding_model returns OpenAIEmbeddings with base_url=LITELLM_BASE_URL."""
    from langchain_openai import OpenAIEmbeddings

    monkeypatch.setattr("src.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")
    monkeypatch.setattr("src.core.config.settings.LITELLM_MASTER_KEY", "sk-test-master")
    monkeypatch.setattr("src.core.config.settings.AI_MODEL_EMBEDDING", "text-embedding-3-large")

    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    emb = svc.get_embedding_model()
    assert isinstance(emb, OpenAIEmbeddings)
    # OpenAIEmbeddings stores openai_api_base or base_url
    base = getattr(emb, "openai_api_base", None) or getattr(emb, "base_url", None)
    assert base == "http://litellm:4000/v1"


def test_litellm_service_generate_response_invokes_chat_model(
    _settings_deepseek_nano: None,
) -> None:
    """generate_response invokes the chat client and returns content string."""
    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

    mock_response = MagicMock()
    mock_response.content = "hola mundo"
    mock_response.response_metadata = {}

    svc = LiteLLMService()
    with patch.object(svc, "_get_chat_model") as mock_get:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get.return_value = mock_client

        result = svc.generate_response(
            messages=[{"role": "user", "content": "hola"}],
            model_type=ModelRole.NANO,
        )
    assert result == "hola mundo"
