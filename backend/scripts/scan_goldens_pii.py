"""PII scanner for golden YAML files (Story D — defense-in-depth).

Standalone CLI script. Imports patterns from ``_pii_patterns.py`` (DRY).

Differences vs scan_seed_pii.py (Story A):
  - Scan path: backend/tests/agentic_evals/sales_agent/goldens/**/*.yaml
  - NO whitelist (spec D10 strict block — synthetic-first invariant has
    no legitimate exceptions; PII in goldens = always a bug).
  - Goldens-specific error message hint.

Design decisions honored:
  D10  — strict block, NO whitelist.
  D-A-3 — imports PATTERNS from _pii_patterns.py (DRY threshold 2 consumers).
  D-A-4 — NO whitelist loading (vs scan_seed_pii.py which reads .eval-whitelist).

Exit codes:
  0  — clean (no PII detected)
  1  — PII detected in one or more files
  2  — error parsing YAML or path does not exist

Usage:
  python backend/scripts/scan_goldens_pii.py [<path>]
  (default path: backend/tests/agentic_evals/sales_agent/goldens/)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from _pii_patterns import DNI_PE_GUARD_PREFIXES, PATTERNS

_DEFAULT_GOLDENS_ROOT: Path = (
    Path(__file__).resolve().parents[1] / "tests" / "agentic_evals" / "sales_agent" / "goldens"
)


# ---------------------------------------------------------------------------
# YAML string traversal
# ---------------------------------------------------------------------------


def _yaml_strings(node: Any, prefix: str = "") -> list[tuple[str, str]]:
    """Recursively collect all string values + their dotted paths.

    Returns list of (yaml_path, string_value) tuples for every string
    leaf in the YAML tree.
    """
    out: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.extend(_yaml_strings(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            out.extend(_yaml_strings(item, f"{prefix}[{i}]"))
    elif isinstance(node, str):
        out.append((prefix, node))
    return out


# ---------------------------------------------------------------------------
# PII detection
# ---------------------------------------------------------------------------


def _check_string(text: str) -> list[tuple[str, str]]:
    """Return list of (pattern_name, matched_text) for all PII matches.

    Applies context guards for dni_pe (8-digit sequences preceded by
    identifier-like context are skipped as false positives).
    """
    hits: list[tuple[str, str]] = []
    for name, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text):
            matched = match.group(0)
            if name == "dni_pe":
                # Context guard: skip if preceded by identifier-like context
                start = match.start()
                preceding = text[max(0, start - 10) : start]
                if any(g in preceding for g in DNI_PE_GUARD_PREFIXES):
                    continue
            hits.append((name, matched))
    return hits


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------


def _scan_file(path: Path) -> list[tuple[str, str, str]]:
    """Scan a single YAML file for PII.

    Returns list of (yaml_path, pattern_name, matched_text) tuples.
    Special: returns [("__error__", "yaml_parse", error_msg)] on parse failure.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.stderr.write(f"ERROR: cannot parse {path}: {exc}\n")
        return [("__error__", "yaml_parse", str(exc))]
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"ERROR: cannot read {path}: {exc}\n")
        return [("__error__", "read_error", str(exc))]

    findings: list[tuple[str, str, str]] = []
    for ypath, value in _yaml_strings(raw):
        for pname, matched in _check_string(value):
            findings.append((ypath, pname, matched))
    return findings


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> int:
    """CLI entrypoint for scan_goldens_pii.py."""
    parser = argparse.ArgumentParser(
        description=(
            "Scan golden YAML files for PII patterns. "
            "Exit 0=clean, 1=PII detected, 2=error. "
            "NO whitelist — strict block (spec D10 synthetic-first invariant)."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        default=_DEFAULT_GOLDENS_ROOT,
        help="Directory to scan recursively for *.yaml files (default: goldens/).",
    )
    args = parser.parse_args()

    scan_path: Path = args.path
    if not scan_path.exists():
        sys.stderr.write(f"ERROR: path does not exist: {scan_path}\n")
        return 2

    if not scan_path.is_dir():
        sys.stderr.write(f"ERROR: '{scan_path}' is not a directory.\n")
        return 2

    yaml_files = sorted(p for p in scan_path.rglob("*.yaml") if "__pycache__" not in p.parts and ".venv" not in p.parts)

    if not yaml_files:
        # Empty directory — no PII possible.
        return 0

    error_count = 0
    pii_count = 0

    for yf in yaml_files:
        findings = _scan_file(yf)
        for ypath, pname, matched in findings:
            if ypath == "__error__":
                error_count += 1
                continue
            pii_count += 1
            try:
                rel = yf.relative_to(scan_path)
            except ValueError:
                rel = yf
            sys.stderr.write(f"PII detected in {rel}:{ypath}: {pname} = {matched!r}\n")

    if error_count:
        return 2

    if pii_count:
        sys.stderr.write(
            f"\n{pii_count} PII match(es) across goldens. "
            "Strict block — synthetic-first invariant requires zero PII.\n"
            "Resolution:\n"
            "  1. Replace real PII with synthetic equivalents (fake names like\n"
            "     'Cliente Ejemplo', phone '+99 0 1234 5678', email 'user@example.com').\n"
            "  2. OR delete the offending golden + regenerate via:\n"
            "     python backend/scripts/generate_golden_candidates.py \\\n"
            "       --tenant <slug> --persona-kind <kind> \\\n"
            "       --output-dir _artifacts/goldens_generation/<run_id>/\n"
            "NO whitelist available for goldens (spec D10).\n"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
