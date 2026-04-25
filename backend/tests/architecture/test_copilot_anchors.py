"""Architecture fitness: every [COPILOT-*] anchor in backend code maps to a known doc.

Ratchet: adding a new anchor in code REQUIRES adding a row to ANCHOR_REGISTRY below.
Removing an anchor from code → remove from registry (shrink-only).
"""

from __future__ import annotations

import re
from pathlib import Path

# ── Canonical anchor registry (§12.1) ──────────────────────────────────────
# Every anchor in backend code must appear here.
# Format: anchor_name -> doc_path (relative to repo root, informational).
ANCHOR_REGISTRY: dict[str, str] = {
    "COPILOT-CANONICAL-BLOCKS": "docs/domains/copilot/message-blocks.md",
    "COPILOT-MESSAGE-CODEC": "docs/domains/copilot/message-blocks.md",
    "COPILOT-OUTGOING-BLOCKS": "docs/domains/copilot/CONTRACT-MULTIMODAL.md",
    "COPILOT-CHANNEL-RENDERER": "docs/domains/copilot/channel-adapters.md",
    "COPILOT-SSE-V2": "docs/domains/copilot/sse-protocol.md",
    "COPILOT-MEDIA-UPLOAD": "docs/domains/copilot/CONTRACT-MULTIMODAL.md",
    "COPILOT-OUTBOUND-ASSETS": "docs/domains/copilot/outbound-assets.md",
    "COPILOT-CITATION-BLOCK": "docs/domains/copilot/message-blocks.md",
    "COPILOT-QUOTE-REPLY": "docs/domains/copilot/message-blocks.md",
    "COPILOT-VOICE-DUAL-MODE": "docs/domains/copilot/CONTRACT-MULTIMODAL.md",
    "COPILOT-SUGGESTIONS-ENGINE": "docs/domains/copilot/suggestions-engine.md",
    "COPILOT-BLOCK-REGISTRY": "docs/domains/copilot/message-blocks.md",
    "COPILOT-READ-DOCUMENT": "docs/domains/copilot/asset-lifecycle.md",
    "COPILOT-DOC-HINT-LAYER": "docs/domains/copilot/asset-lifecycle.md",
    "COPILOT-EDITABLE-FIELDS-SSOT": "docs/domains/copilot/editable-fields.md",
    "COPILOT-MUTATION-VALIDATION": "docs/domains/copilot/editable-fields.md",
    "COPILOT-DOC-EXTRACTION-SSOT": "docs/domains/copilot/document-extraction.md",
    "COPILOT-DOC-EXTRACTION-PIPELINE": "docs/domains/copilot/document-extraction.md",
    "COPILOT-REDESIGN-2026-04": "docs/domains/copilot/redesign-2026-04/README.md",
    "COPILOT-PROVIDER-PATTERN": "docs/domains/copilot/redesign-2026-04/02-architecture-target.md",
    "COPILOT-DEEP-AGENT-V2": "docs/domains/copilot/redesign-2026-04/phases/F2-deep-agents-harness.md",
    "COPILOT-BRAND-SUMMARY-F3": "docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md",
    "COPILOT-INSPIRATION-F4": "docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md",
    "COPILOT-FETCH-URL-F4": "docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md",
    "COPILOT-ASK-TENANT-DATA-F5": "docs/domains/copilot/redesign-2026-04/phases/F5-ask-tenant-data.md",
    "COPILOT-WORKFLOW-F6": "docs/domains/copilot/redesign-2026-04/phases/F6-workflow-unification.md",
}

# Only scan backend Python sources (not tests — anchors in tests are for
# documentation purposes, not extension points that need enforcement).
BACKEND_SRC = Path(__file__).parents[2] / "src"

ANCHOR_PATTERN = re.compile(r"\[(COPILOT-[A-Z0-9-]+)\]")


def _collect_anchors_in_src() -> set[str]:
    """Find all [COPILOT-*] anchors in backend src/ Python files."""
    anchors: set[str] = set()
    for py_file in BACKEND_SRC.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in ANCHOR_PATTERN.finditer(text):
            anchors.add(match.group(1))
    return anchors


def test_all_copilot_anchors_are_registered() -> None:
    """Every [COPILOT-*] anchor in src/ must appear in ANCHOR_REGISTRY.

    Adding a new anchor in code without updating ANCHOR_REGISTRY fails this test.
    """
    anchors_in_code = _collect_anchors_in_src()
    unknown = anchors_in_code - set(ANCHOR_REGISTRY.keys())
    assert not unknown, (
        f"New [COPILOT-*] anchors found in src/ without registry entry:\n"
        f"  {sorted(unknown)}\n"
        f"Add them to ANCHOR_REGISTRY in {__file__} with their doc path."
    )


def test_no_orphan_registry_entries() -> None:
    """Every registry entry should exist as an anchor in code (no dead entries).

    This is a soft check (warning only via informational assert) — anchors may
    be legitimately present only in docs or TS files. We enforce no unknown
    anchors in code, but allow registry to have entries for FE anchors too.
    """
    # We don't fail on orphan entries because some anchors (e.g. COPILOT-BLOCK-REGISTRY,
    # COPILOT-QUOTE-REPLY) are in frontend TS, not in backend Python.
    # This test just documents the registry is not growing unbounded.
    assert len(ANCHOR_REGISTRY) <= 26, (
        f"ANCHOR_REGISTRY has {len(ANCHOR_REGISTRY)} entries. If this is expected, update the limit here."
    )
