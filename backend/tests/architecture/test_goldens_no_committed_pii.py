"""Architecture fitness gate — no PII in committed golden YAML files.

Story D — T-4. Defense-in-depth layer on top of pre-commit hook Section 9.

Runs `scan_goldens_pii.py` against the entire `goldens/` directory and asserts
exit code 0. This gate fires in CI regardless of pre-commit hook presence,
catching any PII that slipped through.

Decision binding:
  D10 — Strict block, NO whitelist. Synthetic-first invariant requires zero PII.
  D-A-4 — NO whitelist loading for goldens (unlike seed scanner).
  pre-commit Section 9 — first line of defense (committed goldens).
  This gate — second line of defense (CI/arch fitness).

Ratchet pattern: empty allowlist, shrink-only.

Skip condition: `goldens/` directory contains no *.yaml files (real curated
goldens not yet committed — typical during builder phase). Gate activates
automatically once Chris promotes the first golden.

# voseo-allowed: arch gate may reference es-AR dialect examples in docstrings
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[3]
_GOLDENS_DIR = _REPO_ROOT / "backend" / "tests" / "agentic_evals" / "sales_agent" / "goldens"
_SCANNER = _REPO_ROOT / "backend" / "scripts" / "scan_goldens_pii.py"


# ---------------------------------------------------------------------------
# PII arch gate
# ---------------------------------------------------------------------------


def test_no_committed_pii_in_goldens() -> None:
    """scan_goldens_pii.py must exit 0 on the entire goldens/ directory.

    Defense-in-depth on top of pre-commit hook Section 9 (T-2).
    Empty allowlist — strict block, synthetic-first invariant.

    Skip when:
    - goldens/ has no *.yaml files (builder phase, real goldens not yet curated)
    - scan_goldens_pii.py not found (T-2 dependency missing)

    Spec: D10, D-A-4, spec Scenario 4 (adversarial PII defense).
    """
    if not _SCANNER.exists():
        pytest.skip(f"scan_goldens_pii.py not found at {_SCANNER}. T-2 prerequisite missing.")

    if not _GOLDENS_DIR.exists():
        pytest.skip(f"goldens/ directory not found: {_GOLDENS_DIR}")

    # Count real golden YAMLs (exclude __init__.py, README.md, _schema.py, etc.)
    real_yamls = [
        p
        for p in _GOLDENS_DIR.rglob("*.yaml")
        if not any(part.startswith(("__", ".")) for part in p.parts)
        # Exclude the smoke golden from Story B (different schema shape)
        and "_schema" not in p.name
    ]

    if not real_yamls:
        pytest.skip(
            "No committed golden YAMLs found in goldens/ directory. "
            "Gate activates once Chris curates and promotes the first golden via promote_golden.py."
        )

    # Run scanner
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(_SCANNER), str(_GOLDENS_DIR)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, (
        f"PII detected in committed goldens (scanner exit {result.returncode}).\n\n"
        f"Scanner stderr:\n{result.stderr}\n"
        "STRICT BLOCK: D10 synthetic-first invariant — zero PII allowed in goldens.\n"
        "NO whitelist available for goldens (D-A-4).\n\n"
        "Resolution:\n"
        "  1. Replace real PII with synthetic equivalents:\n"
        "     - names: 'Cliente Ejemplo', 'Usuario Prueba'\n"
        "     - phones: '+99 0 1234 5678'\n"
        "     - emails: 'user@example.com'\n"
        "  2. OR delete golden + regenerate via generate_golden_candidates.py\n"
        "  3. OR if transcript contains sales_agent voice with natural language that\n"
        "     triggers false positive → add context guard to _pii_patterns.py (T-2 review)\n"
        f"Scanner path: {_SCANNER}\n"
        f"Goldens dir: {_GOLDENS_DIR}"
    )
