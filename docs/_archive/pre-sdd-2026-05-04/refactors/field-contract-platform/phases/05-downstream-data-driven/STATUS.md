---
status: done
opened_at: 2026-04-24
closed_at: 2026-04-24
baseline_green_commit: fc22f528
last_green_commit: d0d121f1
---

# Fase 05 — Downstream data-driven · Status

**Done**. 5 commits + close.

## Sub-steps

| # | Status | Commit | Descripción |
|---|---|---|---|
| 05.A | ✅ done | `94036809` | golden snapshots agent_identity + landing + completion |
| 05.B | ✅ done | `7d0157a4` | sales_agent lifecycle gate via FieldContract |
| 05.C | ✅ done | `37154119` | arch test: agent_identity.j2 paths ⊆ contract |
| 05.D | ✅ done | `0aa7e550` | arch test: completion validators ⊆ contract |
| 05.E | ✅ done | `d0d121f1` | arch test: landing builders ⊆ contract |
| 05.F | ⏭️ skipped | — | sin gaps detectados; 32/36 template paths ya en contract; resto enrichment-only |
| 05.G | ✅ done | (close) | LEARNINGS + STATE/STATUS bump + HANDOFF Fase 06 |

## Diferidos a fase futura

Documented en [LEARNINGS.md Fase 05](../../LEARNINGS.md#fase-05--downstream-data-driven):

1. Reemplazar `{% if offer.X %}` chain por loop sobre contracts en
   `agent_identity.j2` — bloqueado por whitespace handling complexity
   (squashes intencionales).
2. Alineación `is_required_semantic` ↔ `_SECTION_VALIDATORS` —
   bloqueada por divergencia de taxonomy (completion-section ≠ contract-
   section).
3. Migrar landing builders al Offer aggregate (drop raw-SQL en
   `landing_service.generate_landing_for_offer`).
