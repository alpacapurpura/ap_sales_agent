# Handoff — refactor cerrado

> Refactor `field-contract-platform` cerrado tras Fase 09. 6 fases
> (04-09) completadas según plan. Sin handoff a fase siguiente —
> trabajos futuros son product-level dedicados, no parte del refactor.

## Estado final

- **Last green commit**: `f866cd17` (test isolation fix Fase 09).
- **Close commit Fase 09**: pendiente al momento de redactar este doc.
- **Branch**: `development`.
- **Working tree**: limpio (excepto archivos ajenos de sesiones
  paralelas listados en `STATE.md`).

## Resumen agregado

| Métrica | Pre-refactor | Post-refactor |
|---|---|---|
| SSoT paralelos cross-module | 5+ | 1 (`FieldContract` en `shared/domain/`) |
| Módulos migrados al `FieldContract` platform | 0 | 3 (offer + brand + buyer_persona) |
| Copilot read+write surfaces SSoT | divergent (catalog + schema_introspection + offer_fields + 3 catalog projection files) | 1 (FieldContract registry) |
| Algoritmo `next_question` channel-agnostic | inexistente | implementado + testeado |
| `ConversationalChannelPort` para multi-canal | inexistente | abstract + InMemory impl |
| `human_question_es` populated cross-module | offer 25 / brand 0 / buyer 0 | offer 25 / brand 12 / buyer 12 |
| Tests arch totales backend | 432 | 507 (+75 net) |
| Tests cross-module per phase | n/a | 6 fases con +5..+25 cada una |

## Cierre por fase

| Fase | Status | Closing commit |
|---|---|---|
| 04 — Platform foundation | done | `c8ddd79e` |
| 05 — Downstream data-driven | done | `d0d121f1` |
| 06 — Brand migration | done | `bd7bfd31` |
| 07 — Buyer-persona migration | done | `1f210a5d` |
| 08 — Copilot unification | done | `e1f44284` |
| 09 — Multi-channel projection | done | `f866cd17` (close pending) |

## Trabajos futuros (fuera scope este refactor)

Posibles sprints product-level dedicados:

- **Wire copilot↔whatsapp/telegram real**. Requiere copilot
  orchestrator channel-aware + tenant-owner identity en webhook.
  Algoritmo + adapter port + InMemory impl ya listos para drop-in.
- **Diferidos Fase 05** (LEARNINGS Fase 05):
  - Full data-driven loop en `agent_identity.j2` (Python renderer
    custom + override metadata `prompt_label_es`).
  - Completion ↔ contract semantic alignment (override
    `completion_section: str | None`).
  - Migración landing builders al Offer aggregate (drop raw-SQL en
    `landing_service.generate_landing_for_offer`).
- **Walker extension**: list[dict] item sub-keys
  (pain_points.emotional_impact, desires.urgency etc).
- **`human_question_es` enrichment continuo**: solo top required cross-
  module enriquecidos este sprint. Optional fields y todos los offer
  pueden enriquecerse conforme demand del copilot conversacional real.
- **`expects` field hint** populated parcialmente. More enrichment
  posible.

## Referencia rápida — APIs introducidas

```python
# Algoritmo channel-agnostic
from src.modules.copilot.application.orchestrator.conversational_questioning import next_question

contract = next_question("brand", brand_state, section="identity")
# → FieldContract | None

# Hint helper para web (form-runtime guided advance enrichment)
from src.modules.copilot.application.guided.question_hint import build_question_hint

hint = build_question_hint("offer", offer_state, section="strategy")
# → dict {path, section, question_es, expects?} | None

# Channel adapter port (futuro wire-up real)
from src.shared.links.ports.conversational_channel import ConversationalChannelPort
from src.modules.copilot.infrastructure.channels.in_memory_channel import InMemoryConversationalChannel

class WhatsappConversationalChannel(ConversationalChannelPort):
    async def ask(self, contract, *, context=None):
        text = contract.human_question_es or contract.label_es or _humanize(contract.path)
        await self.adapter.send_message(...)
```

## Si retomás trabajo posterior

Cualquier nueva fase = NUEVO refactor con su propio workspace
(`docs/refactors/<nombre>/`). Este refactor no se reabre (INVARIANT 18).

Si se necesita extender el algoritmo / adapter / overrides, tocar los
archivos correspondientes directamente. Tests existentes protegen
regresión (61 unit + 9 cross-module en Fase 09 alone).

## Documentos clave del refactor

- `docs/refactors/field-contract-platform/STATE.md` — pointer final.
- `docs/refactors/field-contract-platform/DESIGN.md` — anchor arquitectónico.
- `docs/refactors/field-contract-platform/DECISIONS.md` — ADR-011..017.
- `docs/refactors/field-contract-platform/LEARNINGS.md` — append-only
  per fase, source of truth para "por qué decidimos X".
- `docs/refactors/field-contract-platform/PLAN.md` — frozen, 6 fases.
- `docs/refactors/field-contract-platform/INVARIANTS.md` — 20 reglas
  inviolables del refactor.
