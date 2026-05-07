"""PII scanner for eval tenant seed YAML files.

Standalone CLI script — no imports from backend/src/. Uses only stdlib
modules: ``re``, ``pathlib``, ``sys``, ``argparse``, and PyYAML.

Design decisions (per 03-arch.md + 05-guidelines.md):
  AD5  — standalone read-only check, orthogonal to shared/sanitization.py.
  AD8  — URL verification schema-only (no HTTP requests).
  AD9  — production_code=false; lives in backend/scripts/, not backend/src/.

Exit codes:
  0  — No PII detected (clean).
  1  — PII detected in one or more files.
  2  — Error parsing a YAML file or the whitelist file.

Usage:
  python backend/scripts/scan_seed_pii.py <path>

Where <path> is a directory. The scanner recurses into subdirectories and
checks all ``*.yaml`` files it finds (excluding the ``.eval-whitelist`` file
itself, which is the whitelist definition).

Whitelist behavior:
  Before flagging a regex match, the scanner checks whether the matched
  string (or its containing line) is covered by ``.eval-whitelist`` in the
  target directory (searched upward). Whitelisted matches are skipped.

Patterns (canonical set from 05-guidelines.md § "Scanner PII"):
  email             — RFC 5322 simplified pattern
  phone_intl        — international phone (+XX format) LatAm/intl
  dni_ar            — Argentine DNI (dotted format: 12.345.678)
  cuit_ar           — Argentine CUIT (XX-XXXXXXXX-X)
  rut_cl            — Chilean RUT (XX.XXX.XXX-K or XX-XXXXXXXX-X)
  dni_pe            — Peruvian DNI (8 consecutive digits, with context guards
                      to reduce false positives — not preceded by = : id=)
  curp_mx           — Mexican CURP (18-char alphanumeric)
  rfc_mx            — Mexican RFC (12-13 char with date embedded)
  url_internal_nicolify — Internal *.nicolify.com URLs (not public references)

Context guards (false positive mitigation per 06-tickets.yaml T-2 note 2):
  dni_pe            — 8 digit sequence preceded by ``=``, ``:``, ``id=``,
                      ``#``, or ``/`` is skipped (likely ID/version string).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# PII pattern catalog (canonical set from 05-guidelines.md)
# ---------------------------------------------------------------------------

PATTERNS: dict[str, str] = {
    "email": r"(?<![a-zA-Z0-9._%+-])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?![a-zA-Z0-9.])",
    "phone_intl": r"(?<![\d])(\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{0,4})(?![\d])",
    "dni_ar": r"(?<![\d.])(\d{1,2}\.\d{3}\.\d{3})(?![\d.])",
    "cuit_ar": r"(?<![\d-])(\d{2}-\d{8}-\d)(?![\d])",
    "rut_cl": r"(?<![\d.])(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])(?![\d.])",
    # DNI-PE: 8 digits NOT preceded by context indicating a non-PII identifier
    # (e.g., database id, hash, URL path segment, version number).
    "dni_pe": r"(?<![=:#/\d])(?<!\bid=)(?<!\brev=)(?<!\bver=)\b(\d{8})\b(?![\d])",
    "curp_mx": r"(?<![A-Z])([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]\d)(?![A-Z\d])",
    "rfc_mx": r"(?<![A-Z])([A-ZÑ&]{3,4}\d{6}[A-Z\d]{3})(?![A-Z\d])",
    "url_internal_nicolify": r"https?://(?:[a-zA-Z0-9-]+\.)*nicolify\.com(?:/[^\s]*)?",
}

_COMPILED: dict[str, re.Pattern[str]] = {name: re.compile(pat) for name, pat in PATTERNS.items()}

# ---------------------------------------------------------------------------
# Whitelist structures
# ---------------------------------------------------------------------------


def _find_whitelist(start_dir: Path) -> Path | None:
    """Search for ``.eval-whitelist`` in start_dir and its parents.

    Returns the first found path, or ``None`` if not found.
    """
    cur = start_dir.resolve()
    for _ in range(6):  # max 6 levels up
        candidate = cur / ".eval-whitelist"
        if candidate.is_file():
            return candidate
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return None


def _load_whitelist(whitelist_path: Path) -> dict[str, Any]:
    """Parse the ``.eval-whitelist`` YAML file.

    Returns a dict with keys:
      whitelisted_urls       — list of {url: str, justification: str}
      whitelisted_email_domains — list of {domain: str, justification: str}
      whitelisted_phone_prefixes — list of {prefix: str, justification: str}
    """
    try:
        raw = yaml.safe_load(whitelist_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to parse whitelist {whitelist_path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(raw, dict):
        return {}
    return raw


def _build_whitelist_sets(
    whitelist: dict[str, Any],
) -> tuple[set[str], set[str], list[str]]:
    """Extract whitelist sets from parsed whitelist dict.

    Returns:
      (whitelisted_url_fragments, whitelisted_email_domains, whitelisted_phone_prefixes)
    """
    urls: set[str] = set()
    for entry in whitelist.get("whitelisted_urls", []):
        if isinstance(entry, dict) and "url" in entry:
            urls.add(entry["url"])

    email_domains: set[str] = set()
    for entry in whitelist.get("whitelisted_email_domains", []):
        if isinstance(entry, dict) and "domain" in entry:
            email_domains.add(entry["domain"].lstrip("@"))  # normalize: store without @

    phone_prefixes: list[str] = []
    for entry in whitelist.get("whitelisted_phone_prefixes", []):
        if isinstance(entry, dict) and "prefix" in entry:
            phone_prefixes.append(entry["prefix"])

    return urls, email_domains, phone_prefixes


# ---------------------------------------------------------------------------
# Match filtering helpers
# ---------------------------------------------------------------------------


def _is_whitelisted_match(
    pattern_name: str,
    match_text: str,
    whitelisted_urls: set[str],
    whitelisted_email_domains: set[str],
    whitelisted_phone_prefixes: list[str],
) -> bool:
    """Return True if a regex match is covered by the whitelist."""
    if pattern_name == "email":
        # Check if the domain part is whitelisted
        at_pos = match_text.find("@")
        if at_pos != -1:
            domain = match_text[at_pos + 1 :]
            if domain in whitelisted_email_domains:
                return True

    elif pattern_name == "phone_intl":
        # Check if the match starts with a whitelisted prefix
        stripped = match_text.strip()
        for prefix in whitelisted_phone_prefixes:
            if stripped.startswith(prefix):
                return True

    elif pattern_name == "url_internal_nicolify":
        # Check if the full URL (or its prefix) is in the whitelisted urls set.
        # This pattern only matches *.nicolify.com URLs, so whitelisted external
        # URLs (visionarias.lat etc.) would never match this pattern anyway.
        for url in whitelisted_urls:
            if match_text.startswith(url) or url.startswith(match_text):
                return True

    return False


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------


def _scan_file(
    path: Path,
    whitelisted_urls: set[str],
    whitelisted_email_domains: set[str],
    whitelisted_phone_prefixes: list[str],
) -> list[tuple[int, str, str]]:
    """Scan a single YAML file for PII matches.

    Returns a list of (line_number, pattern_name, matched_text) tuples
    for each non-whitelisted PII finding.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(2)

    findings: list[tuple[int, str, str]] = []

    for lineno, line in enumerate(content.splitlines(), start=1):
        for pattern_name, compiled in _COMPILED.items():
            for m in compiled.finditer(line):
                matched_text = m.group(0)
                if not _is_whitelisted_match(
                    pattern_name,
                    matched_text,
                    whitelisted_urls,
                    whitelisted_email_domains,
                    whitelisted_phone_prefixes,
                ):
                    findings.append((lineno, pattern_name, matched_text))

    return findings


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------


def scan_directory(target: Path) -> int:
    """Scan all YAML files under ``target`` for PII.

    Loads ``.eval-whitelist`` from ``target`` (or its parents).
    Returns exit code: 0 (clean) or 1 (PII detected).
    """
    whitelist_path = _find_whitelist(target)
    if whitelist_path is not None:
        whitelist = _load_whitelist(whitelist_path)
    else:
        whitelist = {}

    whitelisted_urls, whitelisted_email_domains, whitelisted_phone_prefixes = _build_whitelist_sets(whitelist)

    yaml_files = [
        p
        for p in target.rglob("*.yaml")
        if p.name != ".eval-whitelist" and "__pycache__" not in p.parts and ".venv" not in p.parts
    ]

    if not yaml_files:
        # No YAML files found — nothing to scan, exit clean.
        return 0

    found_pii = False
    for yaml_file in sorted(yaml_files):
        findings = _scan_file(
            yaml_file,
            whitelisted_urls,
            whitelisted_email_domains,
            whitelisted_phone_prefixes,
        )
        for lineno, pattern_name, matched_text in findings:
            rel = yaml_file.relative_to(target) if yaml_file.is_relative_to(target) else yaml_file
            print(f"PII [{pattern_name}] {rel}:{lineno}: {matched_text!r}")
            found_pii = True

    return 1 if found_pii else 0


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entrypoint for scan_seed_pii.py."""
    parser = argparse.ArgumentParser(
        description=("Scan eval seed YAML files for PII patterns. Exit 0=clean, 1=PII detected, 2=error.")
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Directory to scan recursively for *.yaml files.",
    )
    args = parser.parse_args()

    target = args.path.resolve()
    if not target.is_dir():
        print(f"ERROR: '{target}' is not a directory.", file=sys.stderr)
        sys.exit(2)

    exit_code = scan_directory(target)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
