"""Architecture fitness: cada [SALES-AGENT-*] anchor en backend code mapea a un doc registrado.

Mirror del pattern ``test_copilot_anchors.py``. Ratchet: agregar nuevo anchor
en code REQUIERE agregar fila al ANCHOR_REGISTRY abajo.
Quitar anchor del code → quitar del registry (shrink-only).

# [SALES-AGENT-REDESIGN-2026-04 S6]
"""

from __future__ import annotations

import re
from pathlib import Path

# ── Anchor registry canónico ─────────────────────────────────────────────
# Cada anchor en backend code debe aparecer aquí.
# Format: anchor_name -> doc_path (relative to repo root, informational).
ANCHOR_REGISTRY: dict[str, str] = {
    # S3 — cache_boundary refactor
    "SALES-AGENT-CACHE-PREFIX-S3": "docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md",
    # S5 — channel format registry shared
    "SALES-AGENT-CHANNEL-REGISTRY-S5": "docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md",
    # S1 anchors (test fixtures + handler invariants — registrados sin
    # estar en src todavía; reservados para cuando un fixture central los
    # cite).
    "SALES-AGENT-CALLBACK-HANDLER-S1": "docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md",
    "SALES-AGENT-PII-SANITIZE-S1": "docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md",
    # S4 — model role mapping SSoT
    "SALES-AGENT-MODEL-TIER-S4": "docs/domains/sales-agent/redesign-2026-04/phases/S4-chatmodelspec-tier.md",
    # S8 — scheduler tools + workers + webhook entry-points
    "SALES-AGENT-S8-PROVIDER": "docs/domains/sales-agent/redesign-2026-04/phases/S8-tools-scheduler.md",
    "SALES-AGENT-S8-TOOLS": "docs/domains/sales-agent/redesign-2026-04/phases/S8-tools-scheduler.md",
    "SALES-AGENT-S8-CRON": "docs/domains/sales-agent/redesign-2026-04/phases/S8-tools-scheduler.md",
    "SALES-AGENT-S8-WEBHOOK": "docs/domains/sales-agent/redesign-2026-04/phases/S8-tools-scheduler.md",
    # S10 — quality eval loop (LLM judge + goldens + weekly cron + dashboard)
    "SALES-AGENT-QUALITY-S10": "docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md",
    # S11B — orchestrator decomposition (Strangler Fig)
    "SALES-AGENT-AUDIT-EMITTER-S11B": "docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md",
}

ANCHOR_CAP: int = 25
"""Cap soft del crecimiento del registry. Bumpear con justificación cuando
S7+ sume anchors."""

# Sólo escanear backend Python sources (los anchors en tests son
# documentation-only, no extension points).
BACKEND_SRC = Path(__file__).parents[2] / "src"

ANCHOR_PATTERN = re.compile(r"\[(SALES-AGENT-[A-Z0-9-]+)\]")


def _collect_anchors_in_src() -> set[str]:
    """Find all [SALES-AGENT-*] anchors in backend src/ Python files."""
    anchors: set[str] = set()
    for py_file in BACKEND_SRC.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in ANCHOR_PATTERN.finditer(text):
            anchors.add(match.group(1))
    return anchors


def test_all_sales_agent_anchors_are_registered() -> None:
    """Cada [SALES-AGENT-*] anchor en src/ debe aparecer en ANCHOR_REGISTRY.

    Agregar un nuevo anchor en code sin actualizar ANCHOR_REGISTRY falla CI.
    """
    anchors_in_code = _collect_anchors_in_src()
    unknown = anchors_in_code - set(ANCHOR_REGISTRY.keys())
    assert not unknown, (
        f"Nuevos [SALES-AGENT-*] anchors detectados en src/ sin entry en registry:\n"
        f"  {sorted(unknown)}\n"
        f"Agregalos a ANCHOR_REGISTRY en {__file__} con su doc path."
    )


def test_registry_within_cap() -> None:
    """ANCHOR_REGISTRY no debe exceder ANCHOR_CAP sin justificación.

    Bump del cap requiere comentar la razón inline.
    """
    assert len(ANCHOR_REGISTRY) <= ANCHOR_CAP, (
        f"ANCHOR_REGISTRY tiene {len(ANCHOR_REGISTRY)} entries (cap {ANCHOR_CAP}). "
        "Si esto es esperado, bumpea ANCHOR_CAP con justificación inline."
    )
