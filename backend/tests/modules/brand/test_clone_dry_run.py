"""Clone dry-run service tests (B6) — fast parser-only quality gauge.

Research-backed thresholds (Persona-L CHI 2025; PersonaLLM NAACL 2024;
"Catch Me If You Can?" arXiv 2509.14543):
- <10 messages → insufficient (block clone)
- 10-29  → basic (warn weak fidelity)
- 30-99  → decent
- 100+   → strong (pending diversity check)
"""

from __future__ import annotations

import pytest

from src.modules.brand.application.services.personality_service import PersonalityService


@pytest.fixture
def service() -> PersonalityService:
    """A PersonalityService not connected to a real DB — dry_run_clone is pure."""
    from unittest.mock import MagicMock

    return PersonalityService(db=MagicMock())


class TestDryRunMessageCount:
    """Counts parsed messages (post format-detect), not raw lines."""

    def test_insufficient_under_10_messages(self, service: PersonalityService) -> None:
        text = "\n".join(f"Mensaje {i}" for i in range(5))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["message_count"] == 5
        assert result["quality_tier"] == "insufficient"

    def test_basic_at_10_messages(self, service: PersonalityService) -> None:
        text = "\n".join(f"Mensaje {i}" for i in range(15))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["quality_tier"] == "basic"

    def test_decent_at_30_messages(self, service: PersonalityService) -> None:
        text = "\n".join(f"Mensaje {i}" for i in range(45))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["quality_tier"] == "decent"

    def test_strong_at_100_messages(self, service: PersonalityService) -> None:
        text = "\n".join(f"Mensaje {i}" for i in range(120))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["quality_tier"] == "strong"


class TestDryRunFormatDetection:
    """Reports the format the parsers will use downstream."""

    def test_plain_format_for_unstructured_text(self, service: PersonalityService) -> None:
        text = "\n".join(f"Mensaje {i}" for i in range(15))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["detected_format"] == "plain"


class TestDryRunContextCoverage:
    """Surfaces which conversational contexts the material covers."""

    def test_returns_all_5_contexts_in_dict(self, service: PersonalityService) -> None:
        text = "\n".join(f"Mensaje {i}" for i in range(15))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        ctx = result["contexts_detected"]
        assert set(ctx.keys()) == {"greeting", "price", "objection", "closing", "follow_up"}

    def test_detects_greeting_keyword(self, service: PersonalityService) -> None:
        text = "\n".join(["Hola, qué tal", "Buenas tardes", *[f"M{i}" for i in range(13)]])
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["contexts_detected"]["greeting"] >= 2

    def test_detects_objection_keyword(self, service: PersonalityService) -> None:
        text = "\n".join(["Es muy caro para mí", "lo voy a pensar", *[f"M{i}" for i in range(13)]])
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert result["contexts_detected"]["objection"] >= 2

    def test_warns_when_diversity_low_even_at_strong_count(
        self,
        service: PersonalityService,
    ) -> None:
        """100+ greetings with no other context → warning surfaces in recommendation."""
        text = "\n".join("Hola, qué tal" for _ in range(120))
        result = service.dry_run_clone(text_input=text, file_bytes=None)
        assert "cobertura limitada" in result["recommendation"].lower()


class TestDryRunInputs:
    """Mutual exclusion + fallback parity with clone_from_material."""

    def test_raises_when_both_inputs_missing(self, service: PersonalityService) -> None:
        with pytest.raises(ValueError, match="text_input o file_bytes"):
            service.dry_run_clone(text_input=None, file_bytes=None)

    def test_accepts_file_bytes(self, service: PersonalityService) -> None:
        raw = "\n".join(f"M{i}" for i in range(15)).encode("utf-8")
        result = service.dry_run_clone(text_input=None, file_bytes=raw)
        assert result["message_count"] == 15
