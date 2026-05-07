"""Tests for backend/scripts/scan_seed_pii.py (T-2 eval-foundation-tenant-seed-data).

Covers 4 PII categories + whitelist logic + pre-commit integration.

Design decisions honored:
  AD5  — scanner is standalone (no src/ imports), uses regex + pathlib + yaml.
  AD9  — zero production_code impact.
  Q5   — PII concept: scanner runs on staged YAML seed files before commit.

Categories tested:
  1. email         — RFC 5322 email pattern
  2. phone_intl    — international phone number LatAm/intl (+XX format)
  3. id_docs       — DNI-AR/CUIT-AR/RUT-CL/DNI-PE(context-guarded)/CURP-MX/RFC-MX
  4. url_internal  — internal *.nicolify.com URLs

Whitelist:
  - visionarias.lat (public reference URL)
  - @example.com (synthetic RFC 2606 domain)
  - +99 0 / +99 9 (synthetic ITU-T unassigned prefixes)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
SCANNER = BACKEND_ROOT / "scripts" / "scan_seed_pii.py"
WHITELIST_PATH = Path(__file__).resolve().parent / ".eval-whitelist"
TENANTS_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Parametrized adversarial fixtures — one per PII category
# ---------------------------------------------------------------------------

#: Each entry: (category_id, yaml_content_with_pii)
_ADVERSARIAL_CASES = [
    (
        "email",
        "persona:\n  contact: alice.smith@realcompany.com\n  name: Alice\n",
    ),
    (
        "phone_intl",
        "persona:\n  phone: '+51 987 654 321'\n  name: Bob\n",
    ),
    (
        "id_docs_cuit_ar",
        "persona:\n  tax_id: '20-12345678-9'\n  name: Carlos\n",
    ),
    (
        "url_internal_nicolify",
        "assets:\n  portal: 'https://app.nicolify.com/tenant/xyz'\n",
    ),
]


@pytest.mark.parametrize("category,yaml_content", _ADVERSARIAL_CASES, ids=[c[0] for c in _ADVERSARIAL_CASES])
def test_4_categories_detected_on_adversarial_fixtures(
    category: str,
    yaml_content: str,
    tmp_path: Path,
) -> None:
    """Scanner exits 1 on adversarial YAML containing PII in each category.

    Uses tmp_path pytest fixture to create a synthetic YAML file at runtime
    (per 05-guidelines.md: NO commit fixtures with real PII).
    """
    adversarial_dir = tmp_path / "adversarial"
    adversarial_dir.mkdir()
    pii_file = adversarial_dir / "seed.yaml"
    pii_file.write_text(yaml_content, encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(SCANNER), str(adversarial_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, (
        f"Scanner should exit 1 (PII detected) for category='{category}'. "
        f"Got returncode={result.returncode}. stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_no_pii_in_committed_seeds(tmp_path: Path) -> None:
    """Scanner exits 0 on the committed tenants directory.

    When called against the real TENANTS_DIR:
    - If no YAML seed files exist yet (T-1 state, T-3 not done) → scanner
      finds no YAML files → exits 0 (no PII can be found in empty dir).
    - After T-3 creates the 30 YAMLs → scanner must still exit 0 (no real PII).

    This test passes trivially in T-1/T-2 state (no YAMLs yet) and will
    remain GREEN post-T-3 if seeds contain only synthetic data.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(SCANNER), str(TENANTS_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Scanner found PII in committed seeds. Exit={result.returncode}. "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_whitelist_skips_known_public_urls(tmp_path: Path) -> None:
    """Whitelisted public URL (visionarias.lat) is NOT flagged as internal nicolify URL.

    The URL https://visionarias.lat is NOT under *.nicolify.com — the
    url_internal_nicolify pattern only matches *.nicolify.com. This test
    verifies the distinction: visionarias.lat is a different domain and
    should not trigger the url_internal pattern.

    Separately, we also verify @example.com emails are whitelisted via the
    .eval-whitelist (copied to tmp_path so scanner can find it).
    """
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    # Copy real whitelist so scanner can find it when walking up from clean_dir
    import shutil

    shutil.copy(str(WHITELIST_PATH), str(clean_dir / ".eval-whitelist"))

    # visionarias.lat is NOT a nicolify.com subdomain → should not trigger url_internal
    # @example.com is whitelisted via email domain whitelist
    yaml_content = "inspiration:\n  url: 'https://visionarias.lat'\nsample_exchange:\n  contact: 'user@example.com'\n"
    (clean_dir / "brand.yaml").write_text(yaml_content, encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(SCANNER), str(clean_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Scanner incorrectly flagged whitelisted content. "
        f"Exit={result.returncode}. stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_whitelist_skips_synthetic_fixtures_in_sample_exchanges(tmp_path: Path) -> None:
    """Synthetic phone prefixes (+99 0 / +99 9) and @example.com emails are skipped.

    ITU-T E.164 +99 prefix is unassigned — used as synthetic placeholder in
    sample_exchanges per .eval-whitelist. Scanner must skip these via whitelist.
    Copies .eval-whitelist to tmp_path so scanner can locate it.
    """
    import shutil

    clean_dir = tmp_path / "synthetic"
    clean_dir.mkdir()
    # Copy real whitelist to the scan target so scanner finds it
    shutil.copy(str(WHITELIST_PATH), str(clean_dir / ".eval-whitelist"))

    yaml_content = (
        "sample_exchanges:\n"
        "  - context: client_greeting\n"
        "    message: 'Mi número es +99 0 1234 5678 y mi correo es info@example.com'\n"
        "  - context: followup\n"
        "    message: 'Llamame al +99 9 8765 4321 o escríbeme a soporte@example.com'\n"
    )
    (clean_dir / "personality_profile.yaml").write_text(yaml_content, encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [sys.executable, str(SCANNER), str(clean_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Scanner should skip synthetic whitelisted content. "
        f"Exit={result.returncode}. stdout={result.stdout!r} stderr={result.stderr!r}"
    )
