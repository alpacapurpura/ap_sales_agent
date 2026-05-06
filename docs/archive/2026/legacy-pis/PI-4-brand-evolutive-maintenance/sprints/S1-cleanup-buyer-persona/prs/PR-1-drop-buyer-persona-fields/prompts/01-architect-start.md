# Prompt — Architect kickoff (PR-1 drop-buyer-persona-fields)

> Copy-paste este prompt en una nueva sesión Claude Code (o spawn `nicolify-architect` vía Agent tool). PM ya pre-coció contexto.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para PR-1-drop-buyer-persona-fields del PI-4-brand-evolutive-maintenance / S1.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/PR.md` — problema + scope + Surface impactada (tabla con paths exactos del Explore brief)
2. `docs/pm-nico/current-state/brand.md` — capabilities vivas brand
3. `docs/pm-nico/current-state/copilot.md` — capabilities copilot (extraction afectada)
4. `docs/domains/module_brand.md` (si existe) — docs técnicos brand
5. `.claude/rules/backend-ddd.md`, `.claude/rules/tenant-isolation.md`, `.claude/rules/backend-migrations.md`, `.claude/rules/architectural-fitness.md`
6. `.claude/rules/copilot-resilience.md` — guard cleanup copilot
7. Archivos surface (read para entender estructura actual antes diseñar delta):
   - `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py`
   - `backend/src/modules/brand/domain/buyer_persona.py`
   - `backend/src/modules/brand/api/dto/buyer_personas.py`
   - `backend/src/modules/brand/domain/buyer_persona_field_contract.py`
   - `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py`
   - `backend/src/modules/copilot/domain/field_paths_hint.py`
   - `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2`
   - `backend/alembic/versions/f851363921c9_add_buyer_personas.py` (referencia history, NO modificar)

**Skills a invocar (obligatorio):**
- `brand-expert` — guard arquitectura brand schema
- `copilot-expert` — guard cleanup copilot extraction sin romper cache prefix slots ni invariants

**Tu output:** `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/CONTRACT.md` siguiendo template `docs/pm-nico/process/pr-folder-template/CONTRACT.md`.

**El CONTRACT debe especificar:**
1. **Migration plan** — archivo nuevo `backend/alembic/versions/{rev}_drop_buyer_persona_fields.py`. Raw SQL idempotente:
   - `ALTER TABLE buyer_personas DROP COLUMN IF EXISTS objections`
   - `ALTER TABLE buyer_personas DROP COLUMN IF EXISTS preferred_channels`
   - Decidir: 1 migration con 2 ALTER o 2 migrations separadas. Justificar.
   - Decidir: backup data prod antes DROP o aceptar pérdida (verificar con Chris vía PR.md "Decisión técnica abierta"). Si backup → script Python en `scripts/backups/` que dump JSONB columns a JSON file por tenant.
2. **Schema delta BE** — tabla campo-por-campo: archivo + line + cambio (drop column / drop field / drop entry).
3. **Schema delta copilot** — tabla persister + field_paths + extraction template + extraction registry. Verificar slot ordering NO se altera (cache prefix).
4. **Schema delta FE** — tabla schema + types + tests fixtures.
5. **Tests delta** — qué tests existentes deben modificarse, qué tests nuevos agregar (regression: "response no incluye fields", "schema no contiene fields", "migration idempotente").
6. **Open questions for PM** — si detectás algo no anticipado en PR.md (ej: dependencia oculta no listada en surface).

**Reglas:**
- NO escribas código de implementación. Solo schema deltas + decisiones arquitectónicas + plan migration.
- Migration idempotente raw SQL `IF NOT EXISTS` / `IF EXISTS` (regla `backend-migrations.md`).
- Cross-stack: CONTRACT único consumido por BE + FE builders en paralelo.
- Si detectás gap funcional en PR.md → flag en sección "Open questions for PM" y NO inventes solución.
- NO toques `offer.objections` ni `sales_agent.objection_history` (campos distintos, verified Explore).

**Al terminar:**
1. Escribir CONTRACT.md completo.
2. Última línea de tu respuesta debe ser EXACTAMENTE:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-1 architect done" para review. -->`
3. Reportar a Chris brief < 200 palabras: qué decidiste sobre backup data + migration shape + qué quedó como open question.
```

## Cómo usar

1. Chris copia bloque ``` arriba a una nueva sesión Claude Code, o spawn `nicolify-architect` con este texto.
2. Architect produce `CONTRACT.md`. Brief vuelve a Chris.
3. Próxima fase: builders BE+FE paralelos via `prompts/02-builder-start.md`.
