# Prompt — Architect kickoff

> Copy-paste este prompt en una nueva sesión Claude Code (o spawn `nicolify-architect` vía Agent tool). PM ya pre-coció contexto.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para el PR especificado.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-2-suggestions-engine/PR.md` — problema + solución elegida + scope
2. `docs/pm-nico/current-state/copilot.md` — qué existe hoy en el módulo (anti-duplicación)
3. `docs/domains/module_copilot.md` — docs técnicos vivos
4. `.claude/rules/backend-ddd.md` + `.claude/rules/tenant-isolation.md` + `.claude/rules/copilot-resilience.md` + `.claude/rules/copilot-observability.md`
5. `docs/pm-nico/research/2026-04-29-copilot-8-recommendations.md` — origen del problema (#1 en tabla)
6. Código a inspeccionar (read only):
   - `backend/src/modules/copilot/application/tools/offer_section_tools.py` — hint hardcoded a reemplazar
   - `backend/src/modules/copilot/application/orchestrator/block_adapters.py` — registry pattern existente como referencia DDD
   - `backend/src/modules/copilot/observability/` — recorders existentes para hookear `SuggestionShownEvent`

**Skills a invocar (obligatorio):**
- `copilot-expert` — invariantes módulo copilot (resilience + observability + cross-module import excepción)

**Tu output: `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-2-suggestions-engine/CONTRACT.md`** siguiendo template `docs/pm-nico/process/pr-folder-template/CONTRACT.md`.

**Reglas:**
- NO escribas código de implementación. Solo schemas + interfaces + decisiones arquitectónicas.
- Si PR es cross-stack (BE+FE), CONTRACT debe ser ÚNICO consumido por ambos builders en paralelo.
- Usa SQLA 2.0 async + Pydantic v2 + structlog.
- Migrations idempotentes (raw SQL IF NOT EXISTS).
- Cada query con `tenant_id` filter (regla `tenant-isolation.md`).
- response_model obligatorio en cada endpoint.
- Si detectás gap funcional en PR.md → flag en sección "Open questions for PM" y NO inventes solución.

**Al terminar:**
1. Escribir CONTRACT.md completo.
2. Última línea de tu respuesta debe ser EXACTAMENTE:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-2 architect done" para review. -->`
3. Reportar a Chris brief < 200 palabras: qué decidiste + qué quedó como open question.
```

## Cómo usar

1. Reemplazar `2`, `copilot-improvement`, `1`, `2`, `suggestions-engine`, `copilot` con valores reales del PR.
2. PM ya debería tener todo esto pre-llenado al crear el PR.
3. Chris copia y pega en sesión nueva, o spawn `nicolify-architect` con este texto.
