"""Tests for the WhisperTranscriber infrastructure."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.copilot.infrastructure.voice.whisper_transcriber import (
    WhisperTranscriber,
)


@pytest.mark.asyncio
async def test_transcribe_returns_result():
    mock_response = MagicMock()
    mock_response.text = "hola, soy un test de voz"
    mock_response.language = "es"
    mock_response.duration = 3.2

    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(b"fake-audio-bytes", "audio/webm")

        assert result.text == "hola, soy un test de voz"
        assert result.language == "es"
        assert result.duration_seconds == 3.2


@pytest.mark.asyncio
async def test_transcribe_handles_empty_audio():
    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(
            side_effect=Exception("Invalid audio")
        )

        transcriber = WhisperTranscriber()
        with pytest.raises(Exception, match="Invalid audio"):
            await transcriber.transcribe(b"", "audio/webm")


@pytest.mark.asyncio
async def test_transcribe_uses_correct_file_extension():
    """Verify MIME type maps to the correct file extension."""
    mock_response = MagicMock()
    mock_response.text = "test"
    mock_response.language = "en"
    mock_response.duration = 1.0

    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        transcriber = WhisperTranscriber()
        await transcriber.transcribe(b"fake-audio", "audio/mp4")

        call_kwargs = mock_client.audio.transcriptions.create.call_args
        audio_file = call_kwargs.kwargs.get("file") or call_kwargs[1].get("file")
        assert audio_file.name == "recording.mp4"


@pytest.mark.asyncio
async def test_transcribe_defaults_to_webm_for_unknown_mime():
    """Unknown MIME type should default to webm extension."""
    mock_response = MagicMock()
    mock_response.text = "test"
    mock_response.language = "en"
    mock_response.duration = 1.0

    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        transcriber = WhisperTranscriber()
        await transcriber.transcribe(b"fake-audio", "audio/unknown-format")

        call_kwargs = mock_client.audio.transcriptions.create.call_args
        audio_file = call_kwargs.kwargs.get("file") or call_kwargs[1].get("file")
        assert audio_file.name == "recording.webm"


@pytest.mark.asyncio
async def test_transcribe_handles_missing_language():
    """When Whisper returns None for language, default to 'es'."""
    mock_response = MagicMock()
    mock_response.text = "hello"
    mock_response.language = None
    mock_response.duration = 2.0

    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(b"fake-audio", "audio/webm")

        assert result.language == "es"


@pytest.mark.asyncio
async def test_transcribe_handles_missing_duration():
    """When Whisper returns None for duration, default to 0.0."""
    mock_response = MagicMock()
    mock_response.text = "hello"
    mock_response.language = "en"
    mock_response.duration = None

    with patch(
        "src.modules.copilot.infrastructure.voice.whisper_transcriber.openai_client"
    ) as mock_client:
        mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

        transcriber = WhisperTranscriber()
        result = await transcriber.transcribe(b"fake-audio", "audio/webm")

        assert result.duration_seconds == 0.0
