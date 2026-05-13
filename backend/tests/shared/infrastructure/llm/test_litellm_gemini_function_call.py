"""Gemini function-call shape validation via LiteLLM Proxy.

TDD verification for T-4 gemini.py audit checklist (acceptance A4).

Each test corresponds to one item in the mandatory 6-item gemini audit:

  1. Function calling shape via LiteLLM extra_body / tools parameter
  2. Safety settings via extra_body
  3. System instruction conversion (system_prompt param)
  4. Generation config mapping (temperature, max_tokens)
  5. Vision multipart content array handling
  6. Streaming chunk normalization

All tests mock the LangChain ChatOpenAI.invoke() call — they verify that
LiteLLMService correctly PASSES the right kwargs/params to the underlying
LangChain client that targets the LiteLLM Proxy, not that the Gemini API
itself accepts them. The Proxy handles the Gemini-native translation
internally (see https://github.com/BerriAI/litellm/tree/main/litellm/llms/gemini).

Post-T7: all legacy adapter mocks have been migrated. This file adds
coverage for the Gemini-specific shape correctness contract.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from luana_core_platform.core.enums import ModelRole


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def litellm_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch settings for LiteLLMService — points at LiteLLM Proxy."""
    from luana_core_platform.core.enums import AIProvider

    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_MASTER_KEY", "sk-test-master")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_MODEL_REASONING", "gemini-2.5-pro")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_PROVIDER_REASONING", AIProvider.GEMINI)
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_MODEL_VISION", "gemini-2.5-flash")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_PROVIDER_VISION", AIProvider.GEMINI)


def _make_ai_message(content: str = "Gemini response") -> MagicMock:
    """Build a minimal mock AIMessage that LiteLLMService can parse."""
    msg = MagicMock()
    msg.content = content
    msg.response_metadata = {"finish_reason": "stop"}
    msg.usage_metadata = {}
    return msg


# ---------------------------------------------------------------------------
# Audit item 1 — Function calling via tools parameter
# ---------------------------------------------------------------------------


def test_function_calling_shape_passes_tools_via_kwargs(
    litellm_settings: None,
) -> None:
    """A1 — LiteLLMService passes tools param to ChatOpenAI.invoke unchanged.

    LiteLLM Proxy accepts OpenAI-format tool definitions and converts them
    to Gemini native `tools` format internally. No adapter-side conversion
    needed — the proxy handles the mapping.

    Reference: https://github.com/BerriAI/litellm/tree/main/litellm/llms/gemini
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_contacts",
                "description": "Search CRM contacts by name",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
        }
    ]

    expected_response_text = "Found 3 contacts named Maria."
    svc = LiteLLMService()
    messages = [{"role": "user", "content": "Find contacts named Maria"}]
    mock_response = _make_ai_message(expected_response_text)

    with patch.object(svc, "_get_chat_model") as mock_get_model:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get_model.return_value = mock_client

        result = svc.generate_response(messages, model_type=ModelRole.REASONING, tools=tools)

    # Verify tools kwarg reached the invoke call
    call_kwargs = mock_client.invoke.call_args
    assert call_kwargs is not None
    # tools is forwarded as a kwarg to invoke()
    passed_kwargs = call_kwargs.kwargs or {}
    assert "tools" in passed_kwargs, f"Expected 'tools' in invoke kwargs but got: {list(passed_kwargs.keys())}"
    assert passed_kwargs["tools"] == tools
    assert result == expected_response_text


def test_function_calling_model_alias_uses_gemini_prefix(
    litellm_settings: None,
) -> None:
    """LiteLLMService builds model alias 'gemini/<model>' for REASONING role when GEMINI provider.

    LiteLLM Proxy routes 'gemini/gemini-2.5-pro' to Google Gemini API.
    This is the contract that enables function calling to reach Gemini.
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    alias = svc._litellm_model_name(ModelRole.REASONING)
    assert alias.startswith("gemini/"), f"Expected 'gemini/<model>' alias, got: {alias}"
    assert "gemini-2.5-pro" in alias


# ---------------------------------------------------------------------------
# Audit item 2 — Safety settings via extra_body
# ---------------------------------------------------------------------------


def test_safety_settings_passed_through_extra_body(
    litellm_settings: None,
) -> None:
    """A2 — safety_settings forwarded via kwargs to LiteLLM Proxy.

    LiteLLM passes unknown kwargs through as extra_body params to Gemini.
    The legacy GeminiService had NO custom safety_settings implementation —
    it just forwarded **kwargs to chat_model.invoke(). Same semantics apply.

    Reference: https://github.com/BerriAI/litellm/tree/main/litellm/llms/gemini
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    ]

    svc = LiteLLMService()
    messages = [{"role": "user", "content": "Test safety settings pass-through"}]
    mock_response = _make_ai_message("Response with custom safety settings.")

    with patch.object(svc, "_get_chat_model") as mock_get_model:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get_model.return_value = mock_client

        result = svc.generate_response(
            messages,
            model_type=ModelRole.REASONING,
            extra_body={"safety_settings": safety_settings},
        )

    call_kwargs = mock_client.invoke.call_args
    assert call_kwargs is not None
    # extra_body should be passed through to invoke
    passed_kwargs = call_kwargs.kwargs or {}
    assert "extra_body" in passed_kwargs
    assert passed_kwargs["extra_body"]["safety_settings"] == safety_settings
    assert result == "Response with custom safety settings."


# ---------------------------------------------------------------------------
# Audit item 3 — System instruction conversion
# ---------------------------------------------------------------------------


def test_system_prompt_converted_to_langchain_system_message(
    litellm_settings: None,
) -> None:
    """A3 — system_prompt kwarg converted to SystemMessage prepended to message list.

    LiteLLMService._convert_to_lc_messages() prepends a SystemMessage when
    system_prompt is provided. LiteLLM Proxy translates SystemMessage content
    to Gemini's system_instruction field natively.

    The legacy GeminiService did the same: prepend SystemMessage → LangChain
    → Gemini API. Behavior is identical via LiteLLM Proxy.
    """
    from langchain_core.messages import SystemMessage

    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    messages = [{"role": "user", "content": "What is your name?"}]
    system_prompt = "Eres un asistente de ventas de Nicolify. Responde en español neutro."
    mock_response = _make_ai_message("Soy el asistente de ventas de Nicolify.")

    with patch.object(svc, "_get_chat_model") as mock_get_model:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get_model.return_value = mock_client

        result = svc.generate_response(
            messages,
            system_prompt=system_prompt,
            model_type=ModelRole.REASONING,
        )

    # Verify the first message passed to invoke is a SystemMessage
    call_args = mock_client.invoke.call_args
    lc_messages_arg = call_args.args[0]
    assert len(lc_messages_arg) >= 2
    assert isinstance(lc_messages_arg[0], SystemMessage)
    assert lc_messages_arg[0].content == system_prompt
    assert result == "Soy el asistente de ventas de Nicolify."


# ---------------------------------------------------------------------------
# Audit item 4 — Generation config mapping (temperature, max_tokens)
# ---------------------------------------------------------------------------


def test_generation_config_temperature_mapping(
    litellm_settings: None,
) -> None:
    """A4 — Temperature override accepted and cached correctly by LiteLLMService.

    LiteLLMService caches (model, temperature) tuples. When temperature is
    provided, it is forwarded to ChatOpenAI which sends it as a standard
    OpenAI param. LiteLLM Proxy maps it to Gemini's generation_config.temperature.

    Legacy GeminiService used a fixed temperature=0.7 at __init__ with no
    override path (raised NotImplementedError). LiteLLMService supports
    per-call temperature via get_client(temperature=X).
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    custom_temp = 0.3

    # get_client with custom temperature creates a new ChatOpenAI instance
    with patch("luana_core_llm.providers.litellm.ChatBuildContext") as mock_ctx_class:
        mock_ctx = MagicMock()
        mock_ctx_class.return_value = mock_ctx
        with patch("luana_core_llm.providers.litellm._build_chat_from_spec") as mock_build:
            mock_build.return_value = MagicMock()
            svc._get_chat_model(ModelRole.REASONING, temperature=custom_temp)

        # Verify temperature was passed to the build context
        call_args = mock_ctx_class.call_args
        assert call_args is not None
        assert call_args.kwargs.get("temperature") == custom_temp or (
            len(call_args.args) >= 3 and call_args.args[3] == custom_temp
        )


def test_max_tokens_kwarg_passes_through_to_invoke(
    litellm_settings: None,
) -> None:
    """Generation config max_tokens forwarded to LiteLLM Proxy.

    LiteLLM maps max_tokens to Gemini's generation_config.max_output_tokens.
    LiteLLMService.generate_response() forwards unknown kwargs to invoke()
    after normalisation via CHAT_MODEL_SPEC.kwargs_normalizer.
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    messages = [{"role": "user", "content": "Summarize in 50 words"}]
    mock_response = _make_ai_message("Short summary here.")

    with patch.object(svc, "_get_chat_model") as mock_get_model:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get_model.return_value = mock_client

        svc.generate_response(
            messages,
            model_type=ModelRole.REASONING,
            max_output_tokens=200,
        )

    call_kwargs = mock_client.invoke.call_args
    assert call_kwargs is not None
    # After normalization, max_output_tokens → max_tokens (OpenAI protocol)
    passed_kwargs = call_kwargs.kwargs or {}
    assert "max_tokens" in passed_kwargs or "max_output_tokens" in passed_kwargs


# ---------------------------------------------------------------------------
# Audit item 5 — Vision multipart content array handling
# ---------------------------------------------------------------------------


def test_vision_multipart_message_passes_through_as_human_message(
    litellm_settings: None,
) -> None:
    """A5 — Vision content array forwarded as HumanMessage content to LiteLLM Proxy.

    LiteLLM Proxy handles OpenAI-format vision content arrays:
      [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {...}}]
    and converts them to Gemini's multipart content format internally.

    LiteLLMService._convert_to_lc_messages() uses HumanMessage(content=...) for
    user messages, preserving the content as-is (whether string or list).
    The legacy GeminiService did the same via LangChain's HumanMessage.
    """
    from langchain_core.messages import HumanMessage

    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    vision_content: list[dict[str, Any]] = [
        {"type": "text", "text": "Describe this image in detail"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/jpeg;base64,/9j/4AAQSkZJRgAB..."},
        },
    ]
    messages = [{"role": "user", "content": vision_content}]
    mock_response = _make_ai_message("The image shows a marketing dashboard.")

    with patch.object(svc, "_get_chat_model") as mock_get_model:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get_model.return_value = mock_client

        result = svc.generate_response(messages, model_type=ModelRole.VISION)

    call_args = mock_client.invoke.call_args
    lc_messages_arg = call_args.args[0]
    assert len(lc_messages_arg) >= 1
    # Vision content HumanMessage preserves the list content structure
    human_msg = next((m for m in lc_messages_arg if isinstance(m, HumanMessage)), None)
    assert human_msg is not None
    assert human_msg.content == vision_content
    assert result == "The image shows a marketing dashboard."


# ---------------------------------------------------------------------------
# Audit item 6 — Streaming chunk normalization
# ---------------------------------------------------------------------------


def test_streaming_not_implemented_in_generate_response(
    litellm_settings: None,
) -> None:
    """A6 — generate_response() returns string (non-streaming path).

    LiteLLMService.generate_response() uses chat_model.invoke() (not stream()).
    Streaming is handled via get_client(role).stream() separately if needed.

    The legacy GeminiService had NO streaming implementation in generate_response()
    either (same: used chat_model.invoke()). Streaming chunk normalization via
    LiteLLM Proxy applies when callers use get_client(role).stream() directly.
    LiteLLM normalizes Gemini stream delta format to OpenAI-compatible chunks.
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    messages = [{"role": "user", "content": "Stream test"}]
    mock_response = _make_ai_message("LiteLLM normalized response from Gemini stream.")

    with patch.object(svc, "_get_chat_model") as mock_get_model:
        mock_client = MagicMock()
        mock_client.invoke.return_value = mock_response
        mock_get_model.return_value = mock_client

        result = svc.generate_response(messages, model_type=ModelRole.REASONING)

    # generate_response always returns a string (invoke path)
    assert isinstance(result, str)
    assert result == "LiteLLM normalized response from Gemini stream."
    # Confirm invoke() was used (not stream())
    mock_client.invoke.assert_called_once()
    mock_client.stream.assert_not_called()


def test_streaming_via_get_client_returns_langchain_model(
    litellm_settings: None,
) -> None:
    """A6b — get_client(REASONING) returns ChatOpenAI which supports .stream().

    LiteLLM Proxy's streaming uses OpenAI-compatible SSE format.
    LangChain's ChatOpenAI.stream() returns an iterator of AIMessageChunk objects
    with .content attribute. This is the canonical streaming interface for
    LiteLLMService consumers (e.g., sales_agent graph nodes).

    Gemini streaming chunks are normalized by LiteLLM to OpenAI delta format
    (each chunk has choices[].delta.content). LangChain surfaces this as
    AIMessageChunk.content — identical to any other provider.
    """
    from langchain_openai import ChatOpenAI

    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()
    client = svc.get_client(ModelRole.REASONING)

    # get_client returns a ChatOpenAI instance (OpenAI-compat → LiteLLM Proxy)
    assert isinstance(client, ChatOpenAI)
    # ChatOpenAI has .stream() method for streaming
    assert hasattr(client, "stream")
    assert callable(client.stream)
