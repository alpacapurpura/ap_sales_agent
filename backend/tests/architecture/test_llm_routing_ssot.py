"""Architecture guard — LLM routing SSoT enforcement.

Origen: PR-3 PI-2 S2 audit failure 2026-04-30 — capa LLM routing duplicada
introducida en `copilot/infrastructure/llm/` paralela a sistema global
`core/config.py + shared/infrastructure/llm/`.

Este test enforza que SOLO existe un sistema de routing LLM:
- Enum único: `src.core.enums.ModelRole`
- Settings único: `src.core.config.Settings.get_model/get_provider_for_role`
- Providers en: `src.shared.infrastructure.llm.providers/`

Anti-patterns detectados:
- `TIER_METADATA` hardcoded en `copilot/domain/model_tier.py` (legacy, deprecation S3)
- `COPILOT_TIER_*_PROVIDER` env vars (deuda PR-3, eliminar S3)
- Capas LLM nuevas en `modules/<x>/infrastructure/llm/` (NEW LAYER violation)

Allowlist permite legacy en migración. Allowlist shrinks only.

[ANCHOR: docs/domains/llm-routing.md]
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

KNOWN_LEGACY_LLM_FILES: set[str] = set()
"""Allowlist post S3 PR-1 cleanup-modeltier-convergence — target 0 entries reached.

ModelTier eliminado, capa duplicada `copilot/infrastructure/llm/` eliminada,
todos los consumers convergidos a `ModelRole` SSoT. Allowlist ratchet shrink-only:
si test detecta nuevo legacy → fix antes de allowlist.
"""


def _scan_for_pattern(pattern: re.Pattern[str], scope: Path) -> list[str]:
    """Return list of file:line for files matching pattern, excluding allowlist."""
    violations: list[str] = []
    for py_file in scope.rglob("*.py"):
        rel = str(py_file.relative_to(REPO_ROOT))
        if rel in KNOWN_LEGACY_LLM_FILES:
            continue
        if "__pycache__" in rel or rel.endswith(".pyc"):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_num, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if pattern.search(stripped):
                violations.append(f"{rel}:{line_num}: {stripped[:120]}")
    return violations


def test_no_new_modeltier_imports() -> None:
    """ModelTier (legacy) NO debe ser imported fuera de allowlist legacy."""
    pattern = re.compile(
        r"\bfrom\s+src\.modules\.copilot\.domain\.model_tier\s+import|"
        r"\bfrom\s+src\.modules\.copilot\.domain\s+import\s+.*ModelTier"
    )
    violations = _scan_for_pattern(pattern, REPO_ROOT / "src")
    assert not violations, (
        "ModelTier (legacy) imported fuera de allowlist. Use ModelRole from src.core.enums.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_no_copilot_tier_env_vars() -> None:
    """COPILOT_TIER_*_PROVIDER env vars (PR-3 deuda) NO deben aparecer."""
    pattern = re.compile(r"COPILOT_TIER_\w+_(PROVIDER|MODEL_NAME|PRICE_)")
    violations = _scan_for_pattern(pattern, REPO_ROOT / "src")
    assert not violations, (
        "COPILOT_TIER_*_PROVIDER env vars son deuda PR-3 (eliminar S3 PR-1). "
        "Use AI_MODEL_<ROLE> + AI_PROVIDER_<ROLE> from src/core/config.py.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_no_new_llm_factory_layers() -> None:
    """Solo `src/shared/infrastructure/llm/` puede definir LLM factories."""
    forbidden_dirs = [
        REPO_ROOT / "src" / "modules" / "copilot" / "infrastructure" / "llm",
    ]
    violations: list[str] = []
    for d in forbidden_dirs:
        if not d.exists():
            continue
        for py_file in d.rglob("*.py"):
            rel = str(py_file.relative_to(REPO_ROOT))
            if rel in KNOWN_LEGACY_LLM_FILES:
                continue
            violations.append(rel)

    assert not violations, (
        "LLM factories/providers en modules/<x>/infrastructure/llm/ violan NO NEW LAYER rule. "
        "Use src/shared/infrastructure/llm/providers/ + src/core/config.py.\n"
        "See: docs/domains/llm-routing.md\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )
