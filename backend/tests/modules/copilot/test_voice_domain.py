"""Tests for the voice domain ports."""

import pytest

from src.modules.copilot.domain.voice import TranscriptionResult


def test_transcription_result_is_immutable():
    result = TranscriptionResult(text="hola mundo", language="es", duration_seconds=2.5)
    assert result.text == "hola mundo"
    assert result.language == "es"
    assert result.duration_seconds == 2.5


def test_transcription_result_frozen():
    result = TranscriptionResult(text="test", language="en", duration_seconds=1.0)
    with pytest.raises(AttributeError):
        result.text = "changed"
