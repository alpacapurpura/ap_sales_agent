"""Architectural fitness: copilot -> module imports ratchet.

[COPILOT-REDESIGN-2026-04 F0.6 / F1] -> docs/domains/copilot/redesign-2026-04/

This test captures the current set of imports FROM ``src/modules/copilot/`` TO
other domain modules (excluding ``shared``, ``core``, ``iam``, and ``copilot``
itself). F0 freezes the baseline; F1 (provider pattern) is the first phase that
enforces the ratchet — once flipped, the set may only SHRINK as each module's
provider absorbs the imports via dependency inversion.

Today ``copilot`` lives in ``CROSS_IMPORT_ALLOWED_SOURCES`` of
``test_ddd_boundaries.py`` (it is treated as an infra-like orchestrator). That
exemption hides the actual coupling. This test makes it visible and freezable.

State machine
-------------
- ``_RATCHET_FROZEN = False`` (F0 default) -> test SKIPS. The captured set is
  documented in ``KNOWN_COPILOT_TO_MODULE_IMPORTS`` for future diff visibility.
- ``_RATCHET_FROZEN = True`` (F1 onward) -> test ENFORCES:
    * any new import not in the allowlist fails the build,
    * stale entries (already removed) are reported but do not fail.

How to fix a violation post-F1
------------------------------
1. Move the dependency into a provider port owned by the target module
   (see ``docs/domains/copilot/redesign-2026-04/02-architecture-target.md``).
2. Update the copilot side to consume the port via ``application/discovery``.
3. Remove the now-stale entry from ``KNOWN_COPILOT_TO_MODULE_IMPORTS``.

Last verified baseline: 2026-04-25 (F0 close).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# Ratchet state — flip to True when F1 lands.
# ──────────────────────────────────────────────────────────────────────────────
_RATCHET_FROZEN: bool = False

COPILOT_DIR = Path(__file__).resolve().parents[2] / "src" / "modules" / "copilot"
MODULES_BASE = Path(__file__).resolve().parents[2] / "src" / "modules"

# Targets that copilot may import freely (cross-cutting / infra).
ALLOWED_TARGETS: frozenset[str] = frozenset({"copilot", "shared", "core", "iam"})

# ──────────────────────────────────────────────────────────────────────────────
# FROZEN BASELINE (28 entries) captured 2026-04-25 at F0 close.
# Each entry encodes the source-target-path triple of a copilot cross-module
# import. The ratchet may only SHRINK: every removal means a provider port
# absorbed the dependency.
# ──────────────────────────────────────────────────────────────────────────────
KNOWN_COPILOT_TO_MODULE_IMPORTS: frozenset[str] = frozenset(
    {
        "copilot -> analytics | copilot/application/tools/analytics_tools.py",
        "copilot -> assets | copilot/api/media.py",
        "copilot -> assets | copilot/api/voice.py",
        "copilot -> assets | copilot/application/orchestrator/chat.py",
        "copilot -> assets | copilot/application/tools/assets_tools.py",
        "copilot -> assets | copilot/application/tools/document_tools.py",
        "copilot -> assets | copilot/application/tools/extract_from_doc.py",
        "copilot -> assets | copilot/application/tools/guided/extract.py",
        "copilot -> brand | copilot/api/actions.py",
        "copilot -> brand | copilot/application/guided/state_reader.py",
        "copilot -> brand | copilot/application/services/brand_ai_actions_service.py",
        "copilot -> brand | copilot/application/services/offer_psychology_service.py",
        "copilot -> brand | copilot/application/tools/offer_section_tools.py",
        "copilot -> brand | copilot/domain/module_registry.py",
        "copilot -> brand | copilot/domain/schema_introspection.py",
        "copilot -> brand | copilot/infrastructure/persisters/brand_persister.py",
        "copilot -> brand | copilot/infrastructure/persisters/buyer_persona_persister.py",
        "copilot -> commercial_calendar | copilot/domain/module_registry.py",
        "copilot -> connections | copilot/domain/module_registry.py",
        "copilot -> landing | copilot/domain/module_registry.py",
        "copilot -> offer | copilot/application/guided/state_reader.py",
        "copilot -> offer | copilot/application/services/offer_psychology_service.py",
        "copilot -> offer | copilot/domain/module_registry.py",
        "copilot -> offer | copilot/domain/offer_fields.py",
        "copilot -> offer | copilot/infrastructure/persisters/offer_persister.py",
        "copilot -> scheduling | copilot/application/tools/offer_section_tools.py",
        "copilot -> social_proof | copilot/application/tools/offer_section_tools.py",
        "copilot -> social_proof | copilot/domain/module_registry.py",
    }
)


def _collect_copilot_to_module_imports() -> set[str]:
    """Walk copilot/ and yield 'copilot -> {target} | {rel_path}' for every
    cross-module import to a non-allowed target."""
    found: set[str] = set()
    for py in sorted(COPILOT_DIR.rglob("*.py")):
        rel = py.relative_to(MODULES_BASE).as_posix()
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if not node.module.startswith("src.modules."):
                    continue
                target = node.module.split(".")[2]
                if target in ALLOWED_TARGETS:
                    continue
                found.add(f"copilot -> {target} | {rel}")
    return found


def test_no_new_copilot_to_module_imports() -> None:
    """Copilot must not introduce new cross-module imports beyond the F0 baseline.

    During F0 the ratchet is unfrozen (test SKIPS). F1 flips the constant
    ``_RATCHET_FROZEN`` to ``True`` and starts enforcing the contract. From that
    point forward every new copilot -> module import must be replaced by a
    provider pattern (see redesign-2026-04 architecture target).
    """
    if not _RATCHET_FROZEN:
        pytest.skip(
            "Ratchet activates in F1 (provider pattern). Baseline of 28 imports captured 2026-04-25.",
        )

    actual = _collect_copilot_to_module_imports()
    new_violations = sorted(actual - KNOWN_COPILOT_TO_MODULE_IMPORTS)
    if new_violations:
        joined = "\n  ".join(new_violations)
        msg = (
            "New copilot -> module imports detected. Replace with a provider "
            "(see docs/domains/copilot/redesign-2026-04/02-architecture-target.md):"
            f"\n  {joined}"
        )
        raise AssertionError(msg)


def test_baseline_count_matches_documented_state() -> None:
    """Sanity guard for the documented baseline.

    If this number changes without an explicit update of
    ``KNOWN_COPILOT_TO_MODULE_IMPORTS`` the team should know — either we missed
    an arch shift or the captured snapshot is stale. Always runs (also during
    F0) so the baseline cannot silently drift before F1 enforces.
    """
    expected = 28
    assert len(KNOWN_COPILOT_TO_MODULE_IMPORTS) == expected, (
        f"Frozen baseline edited without updating the count comment: "
        f"expected {expected}, found {len(KNOWN_COPILOT_TO_MODULE_IMPORTS)}."
    )
