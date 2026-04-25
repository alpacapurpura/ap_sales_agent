# Prompt — F3 Brand Summary "lighthouse"

> Pegar el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F3 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: crear el documento vivo de marca (`brand_summary` ≤800 chars en español neutro), regenerado por event-driven cuando cambia brand, y auto-inyectado en el system prompt del copilot cuando el route apunta a offer/landing/campaign/sales — sin tocar §3 ni romper golden tests F0/F1/F2.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§4 BrandSummary table + flow)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md  ← APRENDIZAJES F1 (provider pattern hooks)
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md  ← APRENDIZAJES F2 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 2 queries del mandate F3 §3):
    - "LLM brand voice summary distillation prompt 2026 best practices"
    - "event-driven domain events FastAPI ARQ async handler 2026"
    - "OpenAI structured output brand description short concise 2026"
  - Tessl tiles: `tessl__fastapi`, `tessl__pytest-api-testing`. Si surge tile `arq` (workers) o `pydantic-settings`, instalar.
  - Confirmar versión `arq` instalada + última en PyPI. F2 NO la tocó. Si hay diferencia mayor, leer changelog.

- **Foco — no scope creep.** F3 entrega UNA cosa: tabla + worker regen + auto-inyección por route. Tools nuevos del agent (`get_brand_summary`) NO van acá si no aportan al lighthouse — propios para F-pos. URL contextual (F4), `ask_tenant_data` (F5), workflow unification (F6) NO se mezclan.

- **Paso 4 — TDD obligatorio.**
  - Test del worker `regen_brand_summary` con mock LLM (NANO/FAST tier).
  - Test que `BrandContextInjector.inject_for(route, tenant_id)` retorna summary cuando la route matchea + None cuando no.
  - Test que `build_system_prompt(state)` PRE-PENDEA brand_summary cuando aplica (verificar via `state.client_context.current_route` ∈ {offer-studio, landing-studio, campaigns, sales-agent}).
  - Test invariante: el sufijo deep-agent (F2) sigue al final del prompt, no se rompe el orden cacheable.
  - Migración idempotente con clone DB verify.
  - Golden snapshots F1+F2 verdes:
    `cd backend && .venv/bin/pytest tests/modules/copilot/golden/ tests/architecture/test_copilot_provider_compliance.py tests/architecture/test_no_new_copilot_module_imports.py tests/architecture/test_copilot_anchors.py tests/architecture/test_deep_agent_harness_invariants.py tests/modules/copilot/test_deep_agent_harness.py tests/modules/copilot/test_plan_card_emission.py tests/modules/copilot/test_pinned_memory_repository.py -q -o addopts=""`.

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar el orchestrator/brand**: corré los baselines anteriores — debe ser verde (516+ arch tests + 17 golden + tests F2).
  - Después de cada bloque: ruff + golden + arch.
  - Test flaky `test_streaming_integration → tests con db.commit()` heredado F0/F1/F2 (mapper config). Excluir con `--ignore=tests/modules/copilot/test_streaming_integration.py` si rompe random; correr aislado tras tocar streaming/orchestrator.

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card) renderean igual.
  - Cuando la flag `COPILOT_DEEP_AGENT_V2=true`, plan_card sigue saliendo (F2 invariant).
  - Trace recorder registra eventos nuevos si los hay (`brand_summary_regen_started`, `brand_summary_regen_completed`).
  - 4-tier model router intacto. NANO no existe hoy (F8 lo introduce); usar `ModelRole.FAST` para regen.

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (regen ARQ vs sync, prefix vs suffix en system prompt, route allowlist vs siempre).
  - Gotchas reales: si el evento `BrandSectionUpdated` introducido choca con el bus actual.
  - Hooks listos para F4 (URL contextual usa brand_summary para relevancia) y F5 (`ask_tenant_data` puede precargar contexto vía brand_summary).

- **Paso 8 — Generar `prompts/F4-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f3): brand summary lighthouse + auto-inject`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F3-brand-summary-lighthouse.md` y `prompts/F4-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F3 no aplica por aprendizajes F2 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing (incluido el prompt de regen del summary — la salida ES user-facing porque va al system prompt del Copilot).
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F3 (de aprendizajes F2)

### Aprendizajes F2 que F3 debe asumir

- **`build_system_prompt(state)` es el único punto de inyección que cubre legacy + harness deep-agent.** Tanto `agent_node` (legacy) como `build_deep_agent_graph` lo invocan por turno. F3 debe pre-pendear el brand_summary acá, NO en el harness — eso da cobertura sin duplicar.
- **El sufijo deep-agent F2 (`_DEEP_AGENT_SUFFIX_ES` en `deep_agent.py`) viene DESPUÉS del output de `build_system_prompt`.** Para mantener el orden cacheable: brand_summary (estable) → completion snapshot (cambia) → deep-agent suffix (estable). Si F3 cambia el orden, asumir hit-rate de cache cae.
- **`BrandContextInjector.inject_for(target_route, tenant_id)`** ya está declarado en `brand/copilot_provider/context_inject.py` (F1) devolviendo `None`. F3 implementa fetch de `brand_summary` table acá. Provider pattern frozen — NO agregar imports cross-módulo.
- **No existe `ModelRole.NANO` aún** (F8 lo introduce). F3 usa `ModelRole.FAST` (gpt-4o-mini) o introduce alias `FAST_NANO` solo si hace falta diferenciar.
- **Modelos nuevos requieren registro en `tests/conftest.py::db_engine`.** Sin esa fila, los tests pasan solo y rompen suite por mapper config (`LeadModel→TenantModel` lazy fail). Replicar pattern del import F2 `CopilotPinnedMemoryModel`.
- **Migraciones PG con upsert en SQLite**: usar `index_elements=[...]` no `constraint="..."` en `pg_insert.on_conflict_do_update`. Conftest usa SQLite — el segundo rompe.
- **Ratchet `copilot → módulo` frozen en 22 entradas.** F3 no debe agregar imports. Si F3 necesita acceder a brand data: vía `provider_registry` (F1).

### Tests baseline que F3 debe correr ANTES de empezar

```bash
cd backend && .venv/bin/pytest \
  tests/modules/copilot/golden/ \
  tests/architecture/test_copilot_provider_compliance.py \
  tests/architecture/test_no_new_copilot_module_imports.py \
  tests/architecture/test_copilot_anchors.py \
  tests/architecture/test_deep_agent_harness_invariants.py \
  tests/architecture/test_ddd_boundaries.py \
  tests/modules/copilot/test_deep_agent_harness.py \
  tests/modules/copilot/test_plan_card_emission.py \
  tests/modules/copilot/test_pinned_memory_repository.py \
  -q -o addopts="" --timeout=30
```

Debe ser ~60 verde. El flaky `test_streaming_integration` se corre **aislado** post-cambios.

### Archivos clave que F3 modifica (a priori)

- `backend/alembic/versions/068_brand_summary.py` — nueva migración idempotente.
- `backend/src/modules/copilot/infrastructure/models/brand_summary_model.py` — modelo SQLA (registrar en `tests/conftest.py::db_engine`).
- `backend/src/modules/copilot/infrastructure/repositories/brand_summary_repository.py` — CRUD por tenant.
- `backend/src/modules/brand/copilot_provider/summary.py` — `BrandSummaryProvider.summary(tenant_id)` (hoy `None`).
- `backend/src/modules/brand/copilot_provider/context_inject.py` — `BrandContextInjector.inject_for(...)` (hoy `None`).
- `backend/src/shared/events/brand_section_updated.py` — nuevo dominio event.
- `backend/src/shared/workers/brand_summary_regen.py` — ARQ task.
- `backend/src/modules/copilot/application/orchestrator/graph.py::build_system_prompt` — hook donde inyectar el summary como prefix estable (antes del completion_snapshot).
- `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_system.j2` — template recibe nueva variable `brand_summary`.

### Riesgos que vigilar en F3

- **Cache del prompt:** mover el brand_summary al inicio del prompt es lo correcto para cache hit. Pero `completion_snapshot` cambia mucho — si lo dejás detrás del summary, el cache hit del summary es genuino. Confirmar con métrica `cache_creation_input_tokens` antes/después de F3 con flag F2 ON.
- **Regen race condition:** múltiples saves de brand secciones en <60s pueden encolar varias `regen_brand_summary` tasks. Usar lock-per-tenant en ARQ (Redis SETNX o `unique_jobs`) para evitar regeneraciones duplicadas. NO ignorar — la consistencia importa.
- **LLM-judge antes de persistir:** F3 §7 menciona judge. Implementar mínimo (length check + Spanish neutro check via regex de voseo) ANTES de UPSERT. Persistir basura como brand_summary contamina cada turn del Copilot.
- **Eventos cross-module:** si el bus event de Nicolify no maneja eventos brand→workers limpios, F3 puede quedarse atascada. Verificar `src.shared.events.bus` (o equivalente) ANTES de definir `BrandSectionUpdated`. Si no hay bus mature, F3 puede llamar el ARQ task **directamente** desde `BrandRepository.save_section()` (más acoplado pero funcional). Documentar la decisión.
- **Test flaky F0/F1/F2 sigue vivo.** F3 que toca worker/orchestrator: correr aislado el streaming integration tras cambios.
