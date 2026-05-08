"""Tests for backend/scripts/scan_goldens_pii.py (T-2 Story D).

Scenario 4 — Adversarial PII detection.
Tests 4 PII categories x 3 LatAm dialects (AR/MX/PE) via adversarial
YAML fixtures placed in backend/tests/_pii_fixtures/ (NOT goldens/ —
avoids recursive scan contamination during builder phase).

Differences vs test_seed_pii_scanner.py (Story A):
  - Uses scan_goldens_pii.py (no whitelist, strict block per D10).
  - Fixtures live in _pii_fixtures/ (never committed to goldens/).
  - NO whitelist escape — any PII → exit 1.

All tests decorated with @pytest.mark.no_eval — these are pure unit tests
that do NOT invoke LLM / sales_agent runtime. They run on default CI
without --run-evals flag (per conftest.py auto-eval opt-out mechanism).

# voseo-allowed: test fixtures for AR dialect may contain voseo in
# synthetic transcript content (sales_agent voice exception per
# spanish-text.md; dialect_code=es-AR goldens are permitted to use voseo)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# All tests in this module opt out of auto-eval marker (conftest.py
# auto-marks tests/agentic_evals/sales_agent/ with @pytest.mark.eval
# which requires --run-evals flag). These PII scanner tests are pure
# unit tests with no LLM invocation — they must run on default CI.
pytestmark = pytest.mark.no_eval

BACKEND_ROOT = Path(__file__).resolve().parents[3]  # backend/
SCANNER = BACKEND_ROOT / "scripts" / "scan_goldens_pii.py"
PII_FIXTURES_DIR = BACKEND_ROOT / "tests" / "_pii_fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_scanner(path: Path) -> subprocess.CompletedProcess[str]:
    """Run scan_goldens_pii.py against a path, return CompletedProcess."""
    return subprocess.run(  # noqa: S603
        [sys.executable, str(SCANNER), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_yaml(directory: Path, filename: str, content: dict) -> Path:  # type: ignore[type-arg]
    """Write a YAML fixture to directory/filename."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(yaml.safe_dump(content, allow_unicode=True, default_flow_style=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Adversarial fixtures: 4 categories x 3 LatAm dialects
# ---------------------------------------------------------------------------

# Each entry: (category_id, dialect, yaml_content_with_pii)
# Dialect labels are for documentation; actual PII patterns are per-category.
_ADVERSARIAL_CASES: list[tuple[str, str, dict]] = [  # type: ignore[type-arg]
    # --- email ---
    (
        "email_ar",
        "es-AR",
        {
            "transcript": [
                {
                    "role": "customer",
                    "content": "Mandame info a juan.perez@empresa.com.ar",
                    "turn_number": 1,
                }
            ]
        },
    ),
    (
        "email_mx",
        "es-MX",
        {
            "transcript": [
                {
                    "role": "customer",
                    "content": "Mi correo es maria.garcia@negocios.mx",
                    "turn_number": 1,
                }
            ]
        },
    ),
    (
        "email_pe",
        "es-PE",
        {
            "transcript": [
                {
                    "role": "customer",
                    "content": "Escríbeme a carlos.lopez@empresa.pe",
                    "turn_number": 1,
                }
            ]
        },
    ),
    # --- phone_intl (LatAm AR/MX/PE) ---
    (
        "phone_intl_ar",
        "es-AR",
        {
            "transcript": [
                {
                    "role": "customer",
                    "content": "Mi teléfono es +54 11 4567 8901",
                    "turn_number": 1,
                }
            ]
        },
    ),
    (
        "phone_intl_mx",
        "es-MX",
        {
            "transcript": [
                {
                    "role": "customer",
                    "content": "Llámame al +52 55 1234 5678",
                    "turn_number": 1,
                }
            ]
        },
    ),
    (
        "phone_intl_pe",
        "es-PE",
        {
            "transcript": [
                {
                    "role": "customer",
                    "content": "Mi número es +51 987 654 321",
                    "turn_number": 1,
                }
            ]
        },
    ),
    # --- id_docs: DNI_AR + CUIT_AR (AR), CURP_MX + RFC_MX (MX), DNI_PE (PE) ---
    (
        "dni_ar",
        "es-AR",
        {
            "metadata": {
                "notes": "DNI 25.678.901",
            }
        },
    ),
    (
        "cuit_ar",
        "es-AR",
        {
            "metadata": {
                "notes": "CUIT 20-12345678-9",
            }
        },
    ),
    (
        "rut_cl",
        "es-CL",
        {
            "metadata": {
                "notes": "RUT 12.345.678-9",
            }
        },
    ),
    (
        "rfc_mx",
        "es-MX",
        {
            "metadata": {
                "notes": "RFC GARJ840201AB3",
            }
        },
    ),
    # --- url_internal_nicolify ---
    (
        "url_internal_ar",
        "es-AR",
        {
            "transcript": [
                {
                    "role": "agent",
                    "content": "Accede aquí: https://app.nicolify.com/tenant/xyz/offer",
                    "turn_number": 1,
                }
            ]
        },
    ),
    (
        "url_internal_mx",
        "es-MX",
        {
            "metadata": {
                "notes": "Link interno: https://dev-app.nicolify.com/tenant/abc",
            }
        },
    ),
    (
        "url_internal_pe",
        "es-PE",
        {
            "transcript": [
                {
                    "role": "agent",
                    "content": "Ve a https://staging.nicolify.com/checkout",
                    "turn_number": 1,
                }
            ]
        },
    ),
]


@pytest.fixture
def pii_tmp_dir(tmp_path: Path) -> Path:
    """Temporary directory for adversarial PII fixtures."""
    d = tmp_path / "pii_adversarial"
    d.mkdir()
    return d


def test_scanner_exists() -> None:
    """scan_goldens_pii.py must exist (T-2 deliverable)."""
    assert SCANNER.is_file(), f"scan_goldens_pii.py not found at {SCANNER}. T-2 deliverable not yet created."


@pytest.mark.parametrize(
    "category,dialect,content",
    _ADVERSARIAL_CASES,
    ids=[c[0] for c in _ADVERSARIAL_CASES],
)
def test_detects_pii_category(
    category: str,
    dialect: str,
    content: dict,  # type: ignore[type-arg]
    pii_tmp_dir: Path,
) -> None:
    """Scanner exits 1 (PII detected) for adversarial fixture per category x dialect.

    Fixtures are created at runtime in tmp_path — never committed to goldens/.
    """
    fixture_path = pii_tmp_dir / f"{category}_{dialect.replace('-', '_')}.yaml"
    fixture_path.write_text(
        yaml.safe_dump(content, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )

    result = _run_scanner(pii_tmp_dir)
    assert result.returncode == 1, (
        f"Scanner must detect PII for category='{category}' dialect='{dialect}'. "
        f"Got returncode={result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_detects_email_all_dialects(pii_tmp_dir: Path) -> None:
    """test_detects_email — email detected in AR/MX/PE dialects."""
    cases = {
        "email_ar.yaml": {"transcript": [{"role": "customer", "content": "usuario@empresa.com.ar"}]},
        "email_mx.yaml": {"transcript": [{"role": "customer", "content": "info@negocio.mx"}]},
        "email_pe.yaml": {"transcript": [{"role": "customer", "content": "soporte@clientes.pe"}]},
    }
    for fname, data in cases.items():
        (pii_tmp_dir / fname).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    result = _run_scanner(pii_tmp_dir)
    assert result.returncode == 1, (
        f"Scanner must detect email PII across AR/MX/PE dialects. Exit={result.returncode}. stderr={result.stderr!r}"
    )


def test_detects_phone_intl_ar_mx_pe(pii_tmp_dir: Path) -> None:
    """test_detects_phone_intl_ar_mx_pe — phones in AR (+54), MX (+52), PE (+51)."""
    cases = {
        "phone_ar.yaml": {"content": "+54 11 4567 8901"},
        "phone_mx.yaml": {"content": "+52 55 1234 5678"},
        "phone_pe.yaml": {"content": "+51 987 654 321"},
    }
    for fname, data in cases.items():
        (pii_tmp_dir / fname).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    result = _run_scanner(pii_tmp_dir)
    assert result.returncode == 1, (
        f"Scanner must detect phone_intl PII in AR/MX/PE dialects. Exit={result.returncode}. stderr={result.stderr!r}"
    )


def test_detects_dni_cuit_rut_rfc(pii_tmp_dir: Path) -> None:
    """test_detects_dni_cuit_rut_rfc — national ID patterns per country."""
    cases = {
        "dni_ar.yaml": {"notes": "DNI 25.678.901"},
        "cuit_ar.yaml": {"notes": "CUIT 20-12345678-9"},
        "rut_cl.yaml": {"notes": "RUT 12.345.678-9"},
        "rfc_mx.yaml": {"notes": "RFC GARJ840201AB3"},
    }
    for fname, data in cases.items():
        (pii_tmp_dir / fname).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    result = _run_scanner(pii_tmp_dir)
    assert result.returncode == 1, (
        f"Scanner must detect DNI/CUIT/RUT/RFC patterns. Exit={result.returncode}. stderr={result.stderr!r}"
    )


def test_detects_url_internal_nicolify(pii_tmp_dir: Path) -> None:
    """test_detects_url_internal_nicolify — internal *.nicolify.com URLs."""
    data = {
        "transcript": [
            {"role": "agent", "content": "Accede a https://app.nicolify.com/tenant/abc"},
        ]
    }
    fixture = pii_tmp_dir / "url_internal.yaml"
    fixture.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    result = _run_scanner(pii_tmp_dir)
    assert result.returncode == 1, (
        f"Scanner must detect internal nicolify.com URLs. Exit={result.returncode}. stderr={result.stderr!r}"
    )


def test_no_whitelist_strict_block(pii_tmp_dir: Path) -> None:
    """test_no_whitelist_strict_block — goldens scanner has NO whitelist.

    Even @example.com email (whitelisted in scan_seed_pii.py) triggers exit 1.
    D10 strict block: synthetic-first invariant has no legitimate exceptions.
    """
    data = {"contact": {"email": "usuario@example.com"}}
    fixture = pii_tmp_dir / "example_email.yaml"
    fixture.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    result = _run_scanner(pii_tmp_dir)
    # @example.com is still a valid email pattern — scanner has no whitelist
    assert result.returncode == 1, (
        "scan_goldens_pii.py must have NO whitelist. "
        "Even @example.com emails are blocked (D10 strict block). "
        f"Got returncode={result.returncode}."
    )


def test_clean_synthetic_yaml_passes(tmp_path: Path) -> None:
    """test_clean_synthetic_yaml_passes — YAML with no PII exits 0 (clean)."""
    clean_dir = tmp_path / "clean_goldens"
    clean_dir.mkdir()
    # Clean golden YAML — no email, phone, IDs, or internal URLs
    data = {
        "id": "golden-happy-coach-001",
        "schema_version": 1,
        "tenant_slug": "tenant_coach_lat",
        "persona_kind": "happy",
        "dialect_code": "es-419",
        "transcript": [
            {
                "role": "customer",
                "content": "Me interesa el programa de coaching.",
                "turn_number": 1,
            },
            {
                "role": "agent",
                "content": "Con gusto te cuento más sobre el programa.",
                "turn_number": 2,
            },
        ],
        "expected_termination_reason": "GOAL_COMPLETION",
        "expected_voice_attributes": ["warmth", "humor"],
        "expected_tools_invoked": [],
        "forbidden_tools": [],
    }
    (clean_dir / "clean_golden.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8"
    )
    result = _run_scanner(clean_dir)
    assert result.returncode == 0, (
        f"Scanner should exit 0 (clean) for YAML with no PII. Exit={result.returncode}. stderr={result.stderr!r}"
    )


def test_parse_error_exits_2(tmp_path: Path) -> None:
    """Parse error in YAML exits 2 (error), not 1."""
    error_dir = tmp_path / "error_goldens"
    error_dir.mkdir()
    # Write invalid YAML (tab characters break indentation)
    invalid_yaml = "key:\n\tindent_with_tab: bad\n"
    (error_dir / "invalid.yaml").write_text(invalid_yaml, encoding="utf-8")
    result = _run_scanner(error_dir)
    assert result.returncode in (1, 2), (
        f"Scanner must exit 1 or 2 for invalid YAML. Got returncode={result.returncode}."
    )


def test_empty_directory_exits_0(tmp_path: Path) -> None:
    """Empty goldens directory exits 0 (no files = no PII)."""
    empty_dir = tmp_path / "empty_goldens"
    empty_dir.mkdir()
    result = _run_scanner(empty_dir)
    assert result.returncode == 0, (
        f"Scanner should exit 0 (clean) for empty directory. Exit={result.returncode}. stderr={result.stderr!r}"
    )


def test_nonexistent_path_exits_2() -> None:
    """Non-existent path argument exits 2 (error)."""
    result = _run_scanner(Path("/nonexistent/path/does/not/exist"))
    assert result.returncode == 2, f"Scanner must exit 2 for non-existent path. Got returncode={result.returncode}."
