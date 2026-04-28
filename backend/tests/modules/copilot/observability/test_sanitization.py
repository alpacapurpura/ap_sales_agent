"""Tests for PII redaction.

Phase 3 T3.8 — regex-only synchronous redaction. Presidio integration
is deferred to a future async worker (see Phase 3 deferred-debt) so the
hot-path callback handler stays sub-10ms.
"""

from __future__ import annotations


class TestRedactString:
    def test_email_is_partially_masked(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        # Local-part keeps the first letter; domain stays intact for context.
        assert redact_string("contacto: juan@ejemplo.com") == "contacto: j***@ejemplo.com"

    def test_multiple_emails_in_same_string(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        out = redact_string("a@b.com y c@d.org son ambos clientes")
        assert "a***@b.com" in out
        assert "c***@d.org" in out

    def test_phone_latam_with_country_code_is_masked(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        # Peruvian +51 999 888 777 → keep country code, mask the rest.
        out = redact_string("escríbeme al +51 999 888 777")
        assert "+51" in out
        assert "999" not in out
        assert "[REDACTED_PHONE]" in out

    def test_phone_latam_no_country_code(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        out = redact_string("mi numero 999888777 lista")
        assert "999888777" not in out
        assert "[REDACTED_PHONE]" in out

    def test_mexican_phone_with_dash(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        out = redact_string("ll[a]mame al 55-1234-5678")
        assert "55-1234-5678" not in out
        assert "[REDACTED_PHONE]" in out

    def test_openai_api_token(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        out = redact_string("api key: sk-abcDEF123ghiJKL456mnoPQR789")
        assert "sk-abcDEF123ghiJKL456mnoPQR789" not in out
        assert "[REDACTED_TOKEN]" in out

    def test_anthropic_api_token(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        out = redact_string("anthropic key: sk-ant-api03-abcDEF123ghiJKL")
        assert "sk-ant-api03-abcDEF123ghiJKL" not in out
        assert "[REDACTED_TOKEN]" in out

    def test_string_without_pii_is_unchanged(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        original = "Hola, quiero saber más sobre tu producto. Tiene buen precio."
        assert redact_string(original) == original

    def test_short_strings_are_unchanged(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            redact_string,
        )

        assert redact_string("hola") == "hola"
        assert redact_string("") == ""


class TestSanitizePayloadIntegration:
    def test_sanitize_payload_runs_redaction_after_truncate(self) -> None:
        """``sanitize_payload`` should both truncate and redact PII."""
        from src.shared.agent_observability.recording.sanitization import (
            MAX_PAYLOAD_CHARS,
            sanitize_payload,
        )

        payload = {
            "input_messages": "user: ping juan@ejemplo.com please",
            "long": "x" * (MAX_PAYLOAD_CHARS + 100),
            "irrelevant": 42,
            "phone": "+51 999 888 777",
        }
        out = sanitize_payload(payload)

        assert "j***@ejemplo.com" in out["input_messages"]
        assert "juan@ejemplo.com" not in out["input_messages"]
        assert out["long"].endswith(" [truncated]")
        assert out["irrelevant"] == 42
        assert "[REDACTED_PHONE]" in out["phone"]

    def test_sanitize_payload_handles_empty(self) -> None:
        from src.shared.agent_observability.recording.sanitization import (
            sanitize_payload,
        )

        assert sanitize_payload({}) == {}

    def test_redact_value_handles_nested_dicts_and_lists(self) -> None:
        """Top-level shallow walk plus a deep redact for tool args."""
        from src.shared.agent_observability.recording.sanitization import (
            redact_value,
        )

        nested = {
            "args": {
                "email": "boss@empresa.com",
                "items": ["call +51 999 888 777", "ok"],
            },
        }
        out = redact_value(nested)
        assert "boss@empresa.com" not in out["args"]["email"]
        assert "[REDACTED_PHONE]" in out["args"]["items"][0]
