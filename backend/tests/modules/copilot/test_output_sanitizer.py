"""Tests for sanitize_assistant_text — strips JSON blocks from LLM output."""

from __future__ import annotations

from src.modules.copilot.application.orchestrator.output_sanitizer import (
    sanitize_assistant_text,
)


class TestSanitizeAssistantText:
    def test_strips_fenced_json_object(self) -> None:
        text = (
            "Aquí van los resultados:\n"
            '```json\n{"extracted_fields": {"name": "Valeria"}}\n```\n'
            "Listo, revisa el preview."
        )
        cleaned = sanitize_assistant_text(text)
        assert "{" not in cleaned
        assert "extracted_fields" not in cleaned
        assert "revisa el preview" in cleaned.lower()

    def test_strips_fenced_json_array(self) -> None:
        text = 'Cosas:\n```json\n[{"a": 1}, {"a": 2}]\n```\nFinal.'
        cleaned = sanitize_assistant_text(text)
        assert "{" not in cleaned and "[" not in cleaned
        assert "Final" in cleaned

    def test_strips_unfenced_long_object(self) -> None:
        text = (
            'Ok aquí: {"demographics.age_range": "30-42", '
            '"name": "Valeria", "psychographics.values": "Autenticidad"}'
            " — revisa."
        )
        cleaned = sanitize_assistant_text(text)
        assert "demographics" not in cleaned
        assert "revisa" in cleaned

    def test_keeps_short_inline_braces(self) -> None:
        """Short {x} patterns in prose (templates, references) stay intact."""
        text = "El campo {nombre} estará en la ficha."
        cleaned = sanitize_assistant_text(text)
        assert "{nombre}" in cleaned

    def test_keeps_plain_prose(self) -> None:
        text = "Listo, 11 campos están en el preview. Revisa y aprueba."
        assert sanitize_assistant_text(text) == text

    def test_collapses_blank_lines_after_removal(self) -> None:
        text = 'Antes\n\n```json\n{"a": 1}\n```\n\n\nDespués'
        cleaned = sanitize_assistant_text(text)
        assert "\n\n\n" not in cleaned
        assert "Antes" in cleaned and "Después" in cleaned

    def test_empty_input_returns_empty(self) -> None:
        assert sanitize_assistant_text("") == ""

    def test_multiple_fenced_blocks_all_removed(self) -> None:
        text = '```json\n{"a": 1}\n```\nAhora otro:\n```json\n{"b": 2}\n```\nFin.'
        cleaned = sanitize_assistant_text(text)
        assert "{" not in cleaned
        assert "Ahora otro" in cleaned
        assert "Fin" in cleaned
