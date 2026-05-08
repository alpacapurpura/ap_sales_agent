"""Shared PII regex catalog (LIFTED 2026-05-08 from scan_seed_pii.py).

Anti-duplication per .claude/rules/anti-duplication.md — DRY threshold = 2
consumers (scan_seed_pii.py + scan_goldens_pii.py). Lifted to module shared
between scripts.

Backward-compat: scan_seed_pii.py re-imports PATTERNS from this module.
Zero behavior change. Tests in test_seed_pii_scanner.py still pass.

Patterns canonical set (per Story A 05-guidelines.md § "Scanner PII"):
  email, phone_intl, dni_ar, cuit_ar, rut_cl, dni_pe, curp_mx, rfc_mx,
  url_internal_nicolify

Context guards (false positive mitigation):
  dni_pe — 8-digit sequence preceded by =, :, id=, #, / or revision
  prefixes is skipped to avoid flagging database IDs, version strings,
  URL path segments, etc.

Architecture gate: backend/tests/architecture/test_pii_patterns_single_source.py
enforces that BOTH consumers import from this module (DRY invariant).
"""

# downstream-regression-na: scripts/_pii_patterns.py is consumed by
# backend/scripts/scan_seed_pii.py + backend/scripts/scan_goldens_pii.py
# (both in backend/scripts/, not under backend/src/shared/). The downstream
# regression guard in auditor-downstream-regression.md only covers
# backend/src/shared/ surfaces; scripts/ is out of scope.

from __future__ import annotations

from typing import Final

PATTERNS: Final[dict[str, str]] = {
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

# Context guard prefixes for DNI-PE false positive mitigation.
# An 8-digit sequence preceded by these strings is likely a database ID,
# hash, version number, or URL path segment — not a Peruvian DNI number.
DNI_PE_GUARD_PREFIXES: Final[tuple[str, ...]] = ("=", ":", "id=", "#", "/", "version=")


__all__ = ["DNI_PE_GUARD_PREFIXES", "PATTERNS"]
