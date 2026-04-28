"""Architecture fitness — no references to deprecated `/sales/resumen` route.

S00 (sales-agent redesign 2026-04) borró la ruta `/sales/resumen` y sus
componentes orphan (SalesDashboard, ConversionCommandCenter, SalesInboxSheet).
Cualquier reintroducción debe fallar en CI.

Whitelist explícito: `frontend/src/features/growth-studio/**/Resumen*` —
componente DISTINTO (Meta Ads dashboard, activo). NO eliminar.

Si alguna vez la ruta `/sales/resumen` debe re-existir (improbable), agregar
el archivo a `_ALLOWED_LEGACY_REFS` con justificación en el commit.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"

# Patrones prohibidos en cualquier archivo TS/TSX/JS/JSX bajo frontend/src/.
_BANNED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/sales/resumen\b"),
    re.compile(r"\bSalesDashboard\b"),
    re.compile(r"\bConversionCommandCenter\b"),
    re.compile(r"\bSalesInboxSheet\b"),
)

# Whitelist (allowlist ratchet — solo shrink).
# - growth-studio/**/Resumen* = Meta Ads dashboard, feature DIFERENTE de sales/resumen.
# - este propio test menciona los símbolos en su lista de patterns.
_WHITELIST_DIR_PREFIXES: tuple[str, ...] = ("features/growth-studio/",)

_ALLOWED_LEGACY_REFS: frozenset[str] = frozenset()


def _is_target_file(path: Path) -> bool:
    return path.suffix in {".ts", ".tsx", ".js", ".jsx"}


def _is_whitelisted(rel: str) -> bool:
    if rel in _ALLOWED_LEGACY_REFS:
        return True
    return any(rel.startswith(prefix) for prefix in _WHITELIST_DIR_PREFIXES)


@pytest.mark.skipif(
    not FRONTEND_SRC.exists(),
    reason="frontend/src not present — skipping FE arch scan",
)
def test_no_resumen_deprecated_references() -> None:
    """Cero referencias a `/sales/resumen` o componentes orphan post-S00."""
    violations: list[str] = []

    for path in sorted(FRONTEND_SRC.rglob("*")):
        if not path.is_file() or not _is_target_file(path):
            continue
        rel = path.relative_to(FRONTEND_SRC).as_posix()
        if _is_whitelisted(rel):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for pattern in _BANNED_PATTERNS:
            for match in pattern.finditer(content):
                line_no = content.count("\n", 0, match.start()) + 1
                violations.append(
                    f"{rel}:{line_no} → matches {pattern.pattern!r}",
                )

    assert not violations, (
        "Deprecated /sales/resumen references found "
        "(borrado en S00 sales-agent redesign):\n  " + "\n  ".join(violations)
    )
