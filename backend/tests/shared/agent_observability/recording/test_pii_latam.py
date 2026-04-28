"""LATAM PII regex coverage — DNI / CURP / CUIT / RFC / CPF / CC / RUC / CVV / tarjeta.

S1 sales_agent (2026-04-28) extiende `_PII_RES` en
``src/shared/agent_observability/recording/sanitization.py`` con identificadores
LATAM. Keyword guards previenen false-positives sobre UUIDs / decimales /
timestamps / scores. CURP/RFC/CPF formatted son estructuralmente distintivos
(letras + dígitos) y van sin keyword. Bare-dígitos (DNI/CC/DNI PE/RUC/CVV/CUIT
sin guion) requieren keyword cercana.
"""

from __future__ import annotations

import pytest

# Marker constants that the implementation will define.
_NATIONAL_ID_PLACEHOLDER = "[REDACTED_NATIONAL_ID]"
_CARD_PLACEHOLDER = "[REDACTED_CARD]"
_CVV_PLACEHOLDER = "[REDACTED_CVV]"


class TestArgentinaDNI:
    def test_dni_with_keyword_dni(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("mi DNI 38456789 confirmá pagamento")
        assert "38456789" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_dni_with_keyword_documento(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("documento 12345678 listo")
        assert "12345678" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_bare_8_digits_without_keyword_not_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        # Order ID / external_reference style — should NOT be masked.
        original = "external_reference: 38456789 status ok"
        assert redact_string(original) == original


class TestArgentinaCUIT:
    def test_cuit_formatted_dash(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("CUIT del cliente: 20-12345678-9 confirmado")
        assert "20-12345678-9" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_cuil_formatted_dash(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("CUIL 27-87654321-4 listo")
        assert "27-87654321-4" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_cuit_bare_with_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("cuit 20123456789 ok")
        assert "20123456789" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out


class TestMexicoCURP:
    def test_curp_18_chars_no_keyword_needed(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        # Estructuralmente única — letras+fecha+sexo+estado+consonantes+homoclave.
        out = redact_string("registro CURP MARJ900101HDFRRN09")
        assert "MARJ900101HDFRRN09" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_curp_lowercase_is_not_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        # CURP siempre en uppercase oficial — minúsculas son ruido textual.
        original = "marj900101hdfrrn09 (no es curp real)"
        assert redact_string(original) == original


class TestMexicoRFC:
    def test_rfc_persona_13_chars(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("RFC: GODE561231GR8 facturado")
        assert "GODE561231GR8" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_rfc_empresa_12_chars(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("rfc empresa ABC123456789")
        assert "ABC123456789" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out


class TestColombiaCedula:
    def test_cc_with_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("CC 1023456789 verificada")
        assert "1023456789" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_cedula_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("cédula 1023456789 ok")
        assert "1023456789" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out


class TestPeruDNI:
    def test_pe_dni_8_digits_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("DNI 87654321 confirmado")
        assert "87654321" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out


class TestPeruRUC:
    def test_ruc_11_digits_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("RUC 20512345678 facturar")
        assert "20512345678" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out


class TestBrazilCPF:
    def test_cpf_formatted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("CPF do pagador: 123.456.789-09")
        assert "123.456.789-09" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out

    def test_cpf_bare_with_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("cpf 12345678909 ok")
        assert "12345678909" not in out
        assert _NATIONAL_ID_PLACEHOLDER in out


class TestCreditCardNumber:
    def test_card_16_digits_with_spaces(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("tarjeta 4111 1111 1111 1111 listo")
        assert "4111" not in out
        assert _CARD_PLACEHOLDER in out

    def test_card_16_digits_with_dashes(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("4111-1111-1111-1111")
        assert "4111-1111-1111-1111" not in out
        assert _CARD_PLACEHOLDER in out

    def test_card_16_digits_no_separator(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("número 4111111111111111 vence 12/26")
        assert "4111111111111111" not in out
        assert _CARD_PLACEHOLDER in out


class TestCVV:
    def test_cvv_with_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("CVV 123 vencimiento 12/26")
        assert " 123" not in out
        assert _CVV_PLACEHOLDER in out

    def test_cvc_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("cvc 4567 ok")
        assert "4567" not in out
        assert _CVV_PLACEHOLDER in out

    def test_codigo_seguridad_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("código de seguridad 789")
        assert " 789" not in out
        assert _CVV_PLACEHOLDER in out

    def test_bare_3_digits_not_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        # Decimal scores / score thresholds NO deben ser tocados.
        original = "lead_score 850 stage closing"
        assert redact_string(original) == original


class TestNoFalsePositives:
    def test_uuid_not_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        original = "lead_id 9831cfbe-3912-429e-a944-40f3e7bf1372 ok"
        assert redact_string(original) == original

    def test_iso_timestamp_not_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        original = "started_at 2026-04-28T12:34:56Z status ok"
        assert redact_string(original) == original

    def test_decimal_cost_not_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        original = "cost_usd 0.000345 input_tokens 1234"
        assert redact_string(original) == original

    def test_external_reference_8_to_12_digits_no_keyword(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        # Mercado Pago external_reference es 8-32 chars alphanumérico — bare dígitos sin keyword NO masked.
        original = "external_reference: 1234567890123 status approved"
        assert redact_string(original) == original


class TestPaymentLinkURL:
    def test_email_in_query_param_redacted(self) -> None:
        from src.shared.agent_observability.recording.sanitization import redact_string

        out = redact_string("https://mpago.la/abc?payer_email=cliente@example.com")
        assert "cliente@example.com" not in out
        assert "c***@example.com" in out


@pytest.mark.parametrize(
    "raw,must_contain_placeholder",
    [
        ("DNI 38456789", _NATIONAL_ID_PLACEHOLDER),
        ("CURP MARJ900101HDFRRN09", _NATIONAL_ID_PLACEHOLDER),
        ("CUIT 20-12345678-9", _NATIONAL_ID_PLACEHOLDER),
        ("RFC GODE561231GR8", _NATIONAL_ID_PLACEHOLDER),
        ("tarjeta 4111 1111 1111 1111", _CARD_PLACEHOLDER),
        ("CVV 123", _CVV_PLACEHOLDER),
    ],
)
def test_parametrized_latam_pii_coverage(raw: str, must_contain_placeholder: str) -> None:
    from src.shared.agent_observability.recording.sanitization import redact_string

    out = redact_string(raw)
    assert must_contain_placeholder in out
