# Prompt — inicio F4 (URL contextual + Scratchpad inspirations)

> Copiá el bloque entre los `---` literal a una conversación nueva de Claude Code en `/home/chris/AISALESHT`.

---

```
Estamos ejecutando la fase F4 del Copilot Redesign 2026-04 ("Claude Code de Marketing").

Objetivo único de esta fase: tool transversal `fetch_url(url, why?)` que deriva a subagent `url_analyzer` (httpx + trafilatura → markdown → LLM NANO summarize + brand_relevance_score), persiste `/inspirations/{slug}.md` en el scratchpad ephemeral del deep-agent, enriquece el system prompt con tabla de inspiraciones activas (cap 5 FIFO), y habilita `pin_to_memory(path)` para promover al StoreBackend Postgres ya creado en F2 — sin tocar §3 ni romper golden tests F0/F1/F2/F3.

Antes de escribir código, leé en orden (sin saltarte ninguno):
1. docs/domains/copilot/redesign-2026-04/README.md
2. docs/domains/copilot/redesign-2026-04/00-vision-and-non-goals.md  (atención §3 — lista exhaustiva de lo que NO se toca)
3. docs/domains/copilot/redesign-2026-04/01-master-plan.md
4. docs/domains/copilot/redesign-2026-04/02-architecture-target.md  (§1 estructura final, §5 scratchpad híbrido)
5. docs/domains/copilot/redesign-2026-04/03-phase-protocol.md
6. docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md
7. docs/domains/copilot/redesign-2026-04/learnings/F1-provider-pattern.md
8. docs/domains/copilot/redesign-2026-04/learnings/F2-deep-agents-harness.md
9. docs/domains/copilot/redesign-2026-04/learnings/F3-brand-summary-lighthouse.md  ← APRENDIZAJES F3 OBLIGATORIOS

Después seguí los 9 pasos del protocolo (03-phase-protocol.md). Énfasis especial:

- **Paso 2 — Research fresco abril 2026 (no skip).**
  - WebSearch (mínimo 3 queries del mandate F4 §3):
    - "trafilatura python web extraction 2026 best practices markdown"
    - "readability vs trafilatura vs newspaper3k 2026 benchmarks"
    - "httpx async timeout retry web scraping 2026"
    - "LLM url summarization brand alignment scoring 2026"
  - Tessl tiles: `tessl__fastapi`, `tessl__pytest-api-testing`. Si surge tile `trafilatura` o `httpx`, instalar.
  - Confirmar versión `trafilatura` instalada vs PyPI. Si no está instalada, instalar última estable + leer changelog.

- **Foco — no scope creep.** F4 entrega UNA cosa: tool `fetch_url` + subagent `url_analyzer` + scratchpad table en system prompt + `pin_to_memory`. Frontend renderer `inspiration_saved` card opcional si scope lo permite — si no, dejar como nota para F-pos. F5 (`ask_tenant_data`) NO se mezcla.

- **Paso 4 — TDD obligatorio.**
  - Test del subagent `url_analyzer` con HTML fixture (no red).
  - Test que `fetch_url` valida URL (https only, blocklist private/local).
  - Test golden: pegar URL → scratchpad escrito → 2do turn referencia.
  - Test invariante: el sufijo deep-agent (F2) sigue al final del prompt; brand_lighthouse (F3) sigue antes; inspirations table aparece DESPUÉS del lighthouse y ANTES del snapshot completion.
  - Test rate limit (max 10 URLs por conversación).
  - Golden snapshots F1+F2+F3 verdes (correr la suite baseline antes de empezar — comando exacto en learnings F3).

- **Paso 5 — Quality gates native (NUNCA `docker exec`).**
  - **Antes de tocar el orchestrator/scratchpad**: corré la baseline de F0-F3 (~120 tests). Debe ser verde.
  - Después de cada bloque: ruff + golden + arch.
  - Test flaky `test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates` heredados — correr aislados si tocás streaming o editable_fields.

- **Paso 6 — Verificar §3 intacto.**
  - SSE v2 sigue emitiendo block_start/delta/end + message_start/end.
  - Cards (proposal/clarify/preview_update/plan_card) renderean igual.
  - `inspiration_saved` card (si la implementás en FE) extiende, no rompe el contrato existente.
  - Trace recorder registra eventos nuevos si los hay (`url_fetched`, `inspiration_persisted`, `pin_to_memory`).
  - 4-tier model router intacto. Subagent `url_analyzer` usa `ModelRole.FAST` o `MINI` (no inventar `NANO`).

- **Paso 7 — Lecciones aprendidas: ÚTILES, no plantilla rellenada.**
  - Decisiones donde el camino no era único (clarify vs auto-persist, FIFO cap vs LRU, frontmatter shape).
  - Gotchas reales: trafilatura en sitios JS-heavy, anti-bot, query-string strip privacy.
  - Hooks listos para F5 (ask_tenant_data puede leer scratchpad como contexto fuzzy).

- **Paso 8 — Generar `prompts/F5-start.md`** desde plantilla.

- **Paso 9 — Commit + push.**
  - Conventional commit: `feat(copilot-redesign-f4): url contextual + scratchpad inspirations`.
  - Stage por nombre (nunca `git add -A`).
  - Push a `development`.
  - Reportar 3 líneas + paths a `learnings/F4-url-contextual-scratchpad.md` y `prompts/F5-start.md`.

Reglas no negociables:
- Branch único: `development`.
- Brutal honestidad. Si plan F4 no aplica por aprendizajes F3 → flagear y preguntar.
- No alucinar paths/símbolos.
- No tocar §3.
- Native dev tools.
- Spanish neutro LatAm en todo lo user-facing.
- Stage por nombre (parallel-safety).

Empezá por el Paso 1 (releer learnings F1 + F2 + F3). Reportá 3 líneas con qué entendiste antes de Paso 2.
```

---

## Hooks específicos para F4 (de aprendizajes F3)

### Aprendizajes F3 que F4 debe asumir

- **El aggregator de context injectors está en `build_system_prompt(state)`** vía `_collect_context_injectors_prefix(target_route, tenant_id)`. F4 no toca `graph.py` — sólo crea un nuevo `ContextInjector` (en el módulo dueño de las inspirations) que devuelve el bloque "Inspiraciones cargadas" desde `inject_for(...)`. Aparece automáticamente DESPUÉS del brand_lighthouse en el orden discoverty natural.
- **Orden cacheable preservado:** `lighthouse → completion_snapshot/behavior/guided/studio → deep-agent suffix`. F4 inserta inspirations table entre el lighthouse y el snapshot. NO lo metas después del snapshot — la sección snapshot cambia turn-to-turn y romperías el cache hit del lighthouse al insertar volátil entre dos estables.
- **`CopilotPinnedMemoryRepository` (F2) está completo + el módulo+repo ratchet está allowlisted.** F4 implementa `pin_to_memory(path)` tool que lee scratchpad ephemeral, llama `repo.upsert(tenant_id, user_id, path, content, pinned_from_conversation_id)`. Tenant_id/user_id de contextvars (igual que el resto de tools del copilot).
- **Ratchet `copilot → módulo` está frozen en 22.** F4 NO debe agregar imports cross-module a `copilot/application/tools/fetch_url.py` ni al subagent. Las repos brand/landing/etc se acceden vía `provider_registry` (F1).
- **`judge_summary(text)` en `src.shared.workers.brand_summary_regen` valida length cap + voseo regex.** Reusable si el subagent persiste descripciones user-facing (frontmatter, summary del scratchpad). Importarlo o promover a `shared/domain/spanish_neutro_judge.py` si F5 también lo pide.
- **`_await_sync(coro)` en graph.py** corre awaitables desde sync detectando loop activo (FastAPI vs sync test). Reusable si el subagent expone API sync.
- **Modelos nuevos requieren registro en `tests/conftest.py::db_engine`.** Si F4 agrega `InspirationModel` o similar, replicar el patrón F3 (filas 113-114).
- **`pg_insert.on_conflict_do_update` upsert SIEMPRE con `index_elements=[...]`**, nunca `constraint="..."`. SQLite no entiende constraint-named upsert.
- **`CopilotProvider`s descubiertos automáticamente por convención** (`src.modules.{name}.copilot_provider`). F4 sólo implementa `BaseCopilotProvider` subclass + override `context_injector()` o `tool_provider()` según corresponda.

### Tests baseline que F4 debe correr ANTES de empezar

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
  tests/modules/brand/test_brand_summary_repository.py \
  tests/modules/brand/test_brand_section_updated_event.py \
  tests/modules/brand/test_brand_context_injector.py \
  tests/shared/workers/test_brand_summary_regen.py \
  tests/shared/application/test_brand_summary_event_handlers.py \
  tests/modules/copilot/test_brand_lighthouse_in_system_prompt.py \
  -q -o addopts="" --timeout=30
```

Debe ser ~120 verde. El flaky `test_streaming_integration` y `test_editable_fields_ssot::test_no_cross_domain_duplicates` se corren **aislados** post-cambios.

### Archivos clave que F4 modifica (a priori)

- `backend/src/modules/copilot/application/tools/fetch_url.py` — tool transversal nuevo.
- `backend/src/modules/copilot/application/orchestrator/subagents/url_analyzer.py` — subagent dict (TypedDict de deepagents) + lógica.
- `backend/src/modules/copilot/application/orchestrator/subagents/__init__.py` — agregar `URL_ANALYZER_SUBAGENT` al export, `deep_agent.py` lo `extend()`s en `subagents=[...]`.
- `backend/src/modules/copilot/application/tools/pin_to_memory.py` — wrapper de `CopilotPinnedMemoryRepository`.
- `backend/src/modules/copilot/infrastructure/web/trafilatura_client.py` — cliente fetch + extract.
- Posible `backend/src/modules/landing/copilot_provider/context_inject.py` (o ubicación equivalente) — `ContextInjector` que aporta tabla "Inspiraciones cargadas".
- Frontend `frontend/src/features/copilot/components/blocks/InspirationSavedCard.tsx` (si scope lo permite — si no, nota a F-pos).

### Riesgos que vigilar en F4

- **Trafilatura en sitios JS-heavy** (Hotmart, Notion exportadas a HTML) — fallback "no se pudo extraer" + sugerir copy-paste. Playwright fallback queda aplazado; documentar en learnings.
- **Privacy: query strings sensibles** — strip ANTES de persist (`urllib.parse.urlsplit + remove .query`). Audit log debe omitir el query string también.
- **Clarify loop infinito** — cap max 3 questions/url por sesión (consistente con F3 max_clarify_questions del workflow).
- **Cache prefix degradation** — si F4 inserta el bloque inspirations table ENTRE el lighthouse (estable) y el completion snapshot (volátil), el cache hit del lighthouse se mantiene SOLO si la tabla se construye de manera estable mientras el conjunto de inspiraciones no cambia. Si decides regenerarla cada turn (e.g. timestamps "hace 5min"), la cacheabilidad del lighthouse muere también. Diseñar la representación con timestamps relativos pre-formateados o sin timestamps en el system prompt.
- **Test flaky `test_streaming_integration` heredado de F0/F1/F2/F3.** Si F4 toca `streaming` o el orchestrator: correr aislado.
- **Test flaky `test_editable_fields_ssot::test_no_cross_domain_duplicates` heredado** — correr aislado si F4 toca editable_fields registry.
