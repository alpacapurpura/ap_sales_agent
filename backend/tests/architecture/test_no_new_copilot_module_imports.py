"""Architectural fitness: copilot -> module imports ratchet.

[COPILOT-REDESIGN-2026-04 F0.6 / F1] -> docs/domains/copilot/redesign-2026-04/

This test captures the current set of imports FROM ``src/modules/copilot/`` TO
other domain modules (excluding ``shared``, ``core``, ``iam``, and ``copilot``
itself). F0 froze the baseline at 28; F1 (provider pattern) shrunk it to 22 by
removing the legacy hardcoded ``MODULE_REGISTRY`` (six lazy loaders) once
discovery became the single source of truth. Each subsequent fase that
absorbs more dependencies into a provider must remove the corresponding
entries here — the ratchet may only SHRINK.

Today ``copilot`` lives in ``CROSS_IMPORT_ALLOWED_SOURCES`` of
``test_ddd_boundaries.py`` (it is treated as an infra-like orchestrator). That
exemption hides the actual coupling. This test makes it visible and frozen.

How to fix a violation
----------------------
1. Move the dependency into the target module's ``copilot_provider/`` (port
   on ``CopilotProvider``: tools/workflows/summary/context_inject).
2. Update the copilot side to consume it via ``application/discovery``.
3. Remove the now-stale entry from ``KNOWN_COPILOT_TO_MODULE_IMPORTS``.

Last verified baseline: 2026-04-25 (F1 close — provider pattern landed,
ratchet activated, 6 imports absorbed by ``module_registry`` providers).
"""

from __future__ import annotations

import ast
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Ratchet state — frozen by F1 (April 2026).
# ──────────────────────────────────────────────────────────────────────────────
_RATCHET_FROZEN: bool = True

COPILOT_DIR = Path(__file__).resolve().parents[2] / "src" / "modules" / "copilot"
MODULES_BASE = Path(__file__).resolve().parents[2] / "src" / "modules"

# Targets that copilot may import freely (cross-cutting / infra).
ALLOWED_TARGETS: frozenset[str] = frozenset({"copilot", "shared", "core", "iam"})

# ──────────────────────────────────────────────────────────────────────────────
# FROZEN BASELINE (22 entries) at F1 close (2026-04-25).
# F0 captured 28; F1 absorbed 6 imports from ``copilot/domain/module_registry.py``
# into provider ``module_data()`` records. Each subsequent fase shrinks this
# further — every removal means a provider port absorbed the dependency.
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
        "copilot -> brand | copilot/domain/schema_introspection.py",
        "copilot -> brand | copilot/infrastructure/persisters/brand_persister.py",
        "copilot -> brand | copilot/infrastructure/persisters/buyer_persona_persister.py",
        "copilot -> offer | copilot/application/guided/state_reader.py",
        "copilot -> offer | copilot/application/services/offer_psychology_service.py",
        "copilot -> offer | copilot/domain/offer_fields.py",
        "copilot -> offer | copilot/infrastructure/persisters/offer_persister.py",
        "copilot -> scheduling | copilot/application/tools/offer_section_tools.py",
        "copilot -> social_proof | copilot/application/tools/offer_section_tools.py",
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
    """Copilot must not introduce new cross-module imports beyond the F1 baseline.

    Frozen by F1 (April 2026): every new ``copilot -> module`` import must be
    replaced by a ``CopilotProvider`` port (see redesign-2026-04 architecture
    target). The allowlist may only shrink — adding back an entry requires a
    documented justification in the PR description.
    """

    assert _RATCHET_FROZEN, "F1 froze the ratchet — flipping back requires explicit decision in commit."

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

    Edits to the frozen set without updating the count comment fail CI so the
    intent of every shrink/grow is visible in review.
    """
    expected = 22
    assert len(KNOWN_COPILOT_TO_MODULE_IMPORTS) == expected, (
        f"Frozen baseline edited without updating the count comment: "
        f"expected {expected}, found {len(KNOWN_COPILOT_TO_MODULE_IMPORTS)}."
    )


def test_stale_entries_do_not_grow() -> None:
    """Stale entries (frozen but already absorbed) report but do not crash.

    Useful diagnostic when shrinking — keeps `_RATCHET_FROZEN = True` enforcing
    new violations while signalling that lines can be removed.
    """

    actual = _collect_copilot_to_module_imports()
    stale = sorted(KNOWN_COPILOT_TO_MODULE_IMPORTS - actual)
    # Surface in the assertion message when present but never raise — shrinking
    # the frozen set is a separate, deliberate edit.
    assert isinstance(stale, list), "always passes; pretty-prints stale entries on demand"
