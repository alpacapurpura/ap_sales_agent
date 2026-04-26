# Protocolo obligatorio por TP

Toda fase de testing sigue este protocolo. La conversación que ejecuta un TP **debe citar** este doc en su primer paso y aplicarlo end-to-end.

---

## Paso 1 — Re-lectura de contexto (5-10 min)

Antes de tocar código, releer en este orden:

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` — **prestar atención a §3 (lo que NO testeamos)**.
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md` — DAG completo + dónde encaja este TP.
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md` — métricas a medir.
6. `docs/domains/copilot/testing-2026-04/phases/TP{N}-*.md` — la fase actual.
7. `docs/domains/copilot/testing-2026-04/results/TP{N-1}-*.md` (si existe — aprendizajes corrida previa).
8. F# correspondiente del redesign (`docs/domains/copilot/redesign-2026-04/learnings/F{X}-*.md`) — qué prometía la fase implementada.
9. `.claude/rules/copilot-resilience.md` (debug observability) + `.claude/rules/spanish-text.md` (regla 11).

Si algo del plan TP ya no aplica por aprendizajes previos → flagearlo, NO seguir ciego.

---

## Paso 2 — Pre-research fresco (10-20 min, OBLIGATORIO)

> **Estamos en abril 2026.** Best practices de eval cambian rápido (DeepEval pushea releases mensuales, OpenAI cambia pricing trimestral, LangChain rota patrones).

Cada TP tiene en su doc una sección **"Research mandate"** con queries específicas. La conversación DEBE:

- **Web search** mínimo 2 queries del mandate (tool `WebSearch`).
- **Tessl tiles** (skill `tessl-context`) — buscar tiles relevantes (ej. `tessl__pytest-api-testing` para TPs con DeepEval).
- **WebFetch** docs oficiales si la query identificó URLs nuevas (ej. DeepEval changelog, OpenAI pricing page).
- **Si la fase usa una librería específica**, verificar versión más reciente + changelog. No asumir.

Productos del paso 2:

- Lista de fuentes consultadas (irá al `results/`).
- Confirmación o ajuste del enfoque del TP. Si el research sugiere que la solución cambió, el plan se ajusta antes de codear.
- Si descubrís un escenario nuevo crítico, agregarlo a `phases/TP{N}-*.md` antes de ejecutar.

**Anti-pattern:** saltar el research "porque ya sé". El plan se vuelve estancado en días.

---

## Paso 3 — Plan ejecutable (TaskCreate)

Crear tasks granulares con TaskCreate. Una task por escenario o grupo de escenarios relacionados. Cada task ≤2 horas. Marcar dependencias.

Plantilla por task:

- **Subject**: imperativo, concreto. ("Run TP1 scenario S1: short msg routes to NANO").
- **Description**: scenario + assertions + output esperado.
- Status `in_progress` cuando arranca, `completed` cuando los **5 ejes** se midieron.

No hacer lista de 30 tasks. Mantener foco. Nuevos tasks aparecen al avanzar.

---

## Paso 4 — Ejecución por escenario

Por cada escenario del TP:

### 4.1 Setup
- Levantar containers si aplica: `/dev-up` o `docker compose up -d`.
- Confirmar tenant test creado + data poblada según pre-req (varía por TP).
- Limpiar trace buffer si la corrida anterior dejó ruido (`DELETE FROM copilot_trace_event WHERE created_at < NOW() - INTERVAL '1 day'` en local DB si necesario).

### 4.2 Run
Tres modos según el TP:

| Modo | Cuando | Tool |
|---|---|---|
| **Eval-as-code** (DeepEval) | TPs sin UX (TP1, TP2, TP4, TP7, TP8, TP9, TP10) | `cd backend && .venv/bin/pytest tests/quality/deepeval/test_tp{N}_*.py -v -o addopts=""` |
| **Browser live** (Chrome DevTools MCP) | TPs UX (TP3, TP5, TP6, TP11) | Skill `chrome-devtools-verify` con flow scripted |
| **Mixto** | TPs que cubren ambos lados | Eval-as-code primero (regresión cuantitativa), después Chrome DevTools (validación UX) |

### 4.3 Capturar 5 ejes por escenario

**Mandatorio.** Sin los 5 ejes, el escenario no se cierra:

| Eje | Cómo capturarlo |
|---|---|
| **Flujo** | Pass/Fail + descripción de pasos completados. SQL probe a `copilot_trace_event` confirma que todos los nodes esperados emitieron. |
| **Calidad** | DeepEval `assert_test` con métrica + score. CopilotJudge dim scores. |
| **Tokens** | `SELECT data->>'total_tokens', data->>'cached_input_tokens' FROM copilot_trace_event WHERE turn_id = :id AND event_type='turn_end'`. |
| **Latencia** | `data->>'duration_ms'` del turn_end + per-tool. Browser TTFB del Chrome DevTools network panel cuando aplique. |
| **UX** | Sólo cuando aplique (TPs UX). Heurística docs `03-metrics-and-targets.md §UX`. Screenshot si nota algo raro. |

### 4.4 Diagnose + Fix obligatorio

> **Principio rector del plan:** un TP NO se cierra con failures abiertos. La meta no es informar bugs — es entregar la fase del redesign **funcionando** al final del último OK. Cada error detectado se diagnostica hasta root cause y se fixea inline durante la corrida del TP. Si el fix excede el scope arquitectónico del TP (toca otro módulo, otra fase del redesign, otra capa), se aplica igual cuando el bloqueo impide medir el resto del TP — y se documenta en el reporte por qué fue necesario.

Si el escenario falla en cualquier eje:

1. **NO comentar el test.** El fail es señal — perderla destruye el plan.
2. **NO diferir el fix** ("lo abro como ticket, sigo con el resto"). Si el bug bloquea medir otros escenarios del mismo TP → fix YA. Si no bloquea pero está en código que el TP cubre → fix igual.
3. Diagnose en orden:
   - `copilot_trace_event` filtrado a este `turn_id` — buscar `event_type='error'` o tools `status='error'`.
   - `copilot_conversations.messages` (jsonb_pretty) — respuesta cruda del LLM.
   - `docker logs visionarias_brain_dev --tail 200 | grep -i error` — stack traces.
   - Si el síntoma reportado por el user **no aparece en trace** → **bug doble**: el bug original + bug de observabilidad (recorder no capturó). Ambos se fixean (regla `copilot-resilience.md`: "fix el recorder ANTES de investigar el síntoma").
4. Identificar root cause:
   - **Bug arquitectónico** → fix en `src/` siguiendo arquitectura DDD/FSD del redesign. Test debe seguir esperando lo correcto, no lo bugueado.
   - **Test escenario mal diseñado** → corregir escenario en `phases/TP{N}-*.md`. Documentar por qué cambió en el reporte.
   - **Regression vs F#** → cross-check con `learnings/F{X}-*.md`. Si la fase prometía X y ya no entrega X → fix arquitectónico (no abrir ticket diferido).
   - **Dep externa rota** (lib upgrade, API change) → adapter en `src/` o pin temporal con comentario explicando por qué + plan de unblock.
5. **TDD del fix (regla 13 CLAUDE.md):**
   - **a.** Escribir test de regresión que reproduce el bug → RED.
   - **b.** Aplicar fix arquitectónico → GREEN.
   - **c.** Re-correr el escenario TP que detectó el bug → debe pasar.
   - **d.** Quality gates regresión (paso 5) — ningún test preexistente debe romper.
6. Solo entonces se mide el escenario en sus 5 ejes y se cierra.

**Prohibido absoluto:**
- Parchar: `# noqa`, `pytest.skip`, `assert True`, mock que tape el error real.
- Diferir: "abro ticket en `to-do.md` y sigo". `to-do.md` es para mejoras de proceso descubiertas durante el TP, NO para bugs encontrados.
- Cerrar TP con escenario en estado FAIL sin fix aplicado.
- Reportar "bug encontrado, no fixeado por scope" sin haber intentado el fix arquitectónico primero.

**Excepción única:** si el fix demanda cambios cross-stack que requieren coordinación con otra fase del redesign aún no implementada → documentar en `results/TP{N}-{fecha}.md §Fixes diferidos` con: root cause exacto, archivo+línea, plan arquitectónico del fix, qué fase del redesign lo destraba, y aplicar workaround temporal con comentario `# TODO(TP{N}-fix-pending): …` que el quality gate de la próxima corrida valida que se removió. Esta excepción se justifica al user antes de aplicarla, no después.

---

## Paso 5 — Quality gates regresión

Si el TP modificó código de producción (fix arquitectónico):

```bash
# Backend
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q

# Frontend (si tocó FE)
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/
```

Si **algo** falla, no se cierra TP. Se arregla o se revierte el bloque problemático.

---

## Paso 6 — Reporte (`results/TP{N}-{YYYY-MM-DD}.md`)

Crear `results/TP{N}-{fecha}.md` con la plantilla de `02-test-plan.md §Outputs`:

```markdown
# TP{N} — {fecha}

## Pre-research
- {fuente1} — qué cambió mi enfoque.
- {fuente2}

## Scenarios run
| ID | Descripción | Pass/Fail | Cost ($) | Latencia (ms) | Judge avg | Notas UX |
|---|---|---|---|---|---|---|
| S1 | … | ✅ | 0.003 | 720 | 4.2 | — |
| S2 | … | ❌ | 0.012 | 1840 | 2.8 | flash-of-empty |

## Diff vs baseline
- Latencia p50: 720ms vs target 800ms ✅.
- Cost/turn promedio: $0.004 vs target $0.005 ✅.
- Judge avg: 3.9 vs target 4.0 ⚠ (S5 tira el promedio abajo).

## Failures + root cause
### S2 — flash-of-empty card
- **Síntoma:** card aparece, parpadea, desaparece, reaparece.
- **Trace evidence:** dos `card_emitted` consecutivos con mismo card_kind (`copilot_trace_event WHERE turn_id=…`).
- **Root cause:** `_handle_tool_end_v2` emite block_append + `_maybe_emit_plan_card` también emite, sin dedupe por card_id.
- **Fix:** … (path + diff resumen) o → "fix excede scope, abierto F12.b en TP{X}".

## Recomendaciones
- TP{N+1} debe revisar también X.
- Considerar agregar escenario S6 a la siguiente corrida.

## Métricas agregadas
- Cost total run: $0.087 (15 escenarios).
- Latencia p50: 720ms / p95: 1840ms.
- Judge avg cross-scenarios: 3.9.

## Aprendizajes para TP{N+1}
- {1-3 bullets MAX, hecho concreto + cómo aplica al TP siguiente}
- Si no hay aprendizajes accionables, omitir sección entera (no llenar por llenar).

## Handoff TP{N+1}

Prompt copy-paste para TP{N+1} vive en `docs/domains/copilot/testing-2026-04/prompts/TP{N+1}-start.md` (convención del plan: prompts en `prompts/`, no embedded en `results/`). Generado siguiendo el template canónico §Anexo A.
```

---

## Paso 7 — Actualizar `phases/TP{N}-*.md` si aprendiste

Si durante la corrida descubriste:

- Escenarios nuevos críticos → agregar a la sección **"Scenarios"** del doc del TP.
- Tools/queries nuevas que sirvieron → agregar a **"Tools / queries"**.
- Targets erróneos (ej. "p50 ≤500ms" era irreal, debe ser ≤800ms) → bumpear con justificación en commit.
- Anti-patterns descubiertos → agregar a **"Antipatrones"**.

El plan vive. NO es write-once. La próxima corrida del mismo TP arranca más inteligente.

---

## Paso 8 — Commit + push (cuando hay fixes / docs nuevos)

Si tocaste código o updateaste docs:

- Commit conventional: `test(copilot-tp{N}): {scope corto}` o `fix(copilot-{module}): {root cause} (TP{N})`.
- Cuerpo menciona: TP que originó el fix + scenario ID + path al `results/`.
- Push a `development` (parallel-safety: stage por nombre, nunca `git add -A`).

---

## Paso 9 — Generar prompt TP{N+1} (OBLIGATORIO)

Antes de cerrar la conversación TP{N}, dos artefactos OBLIGATORIOS:

1. `results/TP{N}-{fecha}.md` incluye sección **"Aprendizajes para TP{N+1}"** (1-3 bullets accionables o omitir si no hay) + sección **"Handoff TP{N+1}"** que apunta al archivo del prompt.
2. `prompts/TP{N+1}-start.md` con el fenced block listo para copy-paste, generado siguiendo el template canónico §Anexo A.

**Convención:** los prompts viven en `prompts/`, NO embebidos en `results/`. El reporte sólo referencia el path. Razón: el archivo dedicado es greppeable por TP, evita que el reporte crezca >300 líneas, y permite editar el prompt sin tocar el reporte (que es snapshot del run).

El usuario abre `prompts/TP{N+1}-start.md`, copia el fenced block a una conversación nueva → TP{N+1} arranca self-contained.

Si TP{N} es el último de la serie (e.g. TP11), reemplazar el handoff por sección **"Cierre del plan"** en el reporte con resumen agregado de los 12 TPs + decisión sobre TP repeat / nueva ronda / archivo del plan. NO se genera `prompts/TP12-start.md`.

---

## Reglas anti-deriva (críticas)

1. **No agregar scope** del TP en términos de escenarios nuevos. Si descubrís oportunidad → al `results/` como recomendación, NO al código.
2. **No tocar §3 (lo que NO testeamos).** Si parece necesario → parar, preguntar al usuario.
3. **No alucinar.** Si no estás seguro de un path/símbolo → leer el archivo, no inventar.
4. **No skip pre-research.** Aunque "creas saber" — abril 2026, siempre algo cambió.
5. **No cerrar TP sin los 5 ejes** medidos por escenario.
6. **No tocar otros módulos sin que sigan funcionando** (regla redesign).
7. **No parchar.** Root cause obligatorio (paso 4.4).
8. **No diferir fixes.** Bugs detectados durante el TP se arreglan en el TP. Solo se difieren con la excepción documentada en §4.4 y aprobación previa del user.
9. **El TP termina con código verde.** Último OK = redesign funcionando, no informe de pendientes.
10. **Commit reportes en `results/`** — los reportes son parte del producto del plan.
11. **Cierre handoff obligatorio.** Cada TP termina entregando el prompt completo del siguiente (§Anexo A). El usuario no debe reconstruir contexto entre fases.

---

## Anexo A — Template canónico del prompt TP{N+1}

Cada TP{N} cierra generando esta estructura en `prompts/TP{N+1}-start.md`. El prompt va dentro de un fenced code block para copy-paste limpio. El reporte `results/TP{N}-{fecha}.md` sólo agrega sección **"Handoff TP{N+1}"** que referencia el path del archivo.

```markdown
Iniciar TP{N+1} plan testing-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión TP{N+1}

{1-3 líneas: qué F# valida + qué confirma. Copiar de `phases/TP{N+1}-*.md §Misión`.}

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md` (§3 lo que NO testeamos)
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md`
7. `docs/domains/copilot/testing-2026-04/phases/TP{N+1}-*.md`
8. `docs/domains/copilot/testing-2026-04/results/TP{N}-{fecha}.md` (aprendizajes + cualquier change a `phases/`)
9. `docs/domains/copilot/redesign-2026-04/learnings/F{X}-*.md` (la fase del redesign que valida — listada en `02-test-plan.md`)
10. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`

## Pre-research obligatorio (paso 2 protocolo)

Mínimo 2 web searches del mandate listado en `phases/TP{N+1}-*.md §Research mandate`. Tessl tiles: skill `tessl-context` para librerías nuevas/relevantes.

Si descubrís escenario crítico no listado en TP{N+1} doc, agregalo a `phases/TP{N+1}-*.md` ANTES ejecutar.

## Setup heredado (NO rehacer — verificado en TP1 setup)

- Migraciones aplicadas hasta head (`alembic current` en `visionarias_brain_dev`)
- DeepEval 3.9.7 native venv + docker dev
- `backend/tests/quality/deepeval/` skeleton + conftest opt-in (`RUN_DEEPEVAL=1`)
- Conftest fixes: `model_registry` import + `_isolate_trace_recorder_db` autouse
- Helper Clerk: `backend/scripts/get_clerk_test_token.py` (cache /tmp + auto-refresh)
- `.env`: `CLERK_TEST_SESSION_ID` + `CLERK_SECRET_KEY` + `OPENAI_API_KEY`
- Tenant test: `9ba0b29a-8507-424f-a48a-896f93218a25` (visionarias-v4)
- Bugs arch fixeados en TP1: deep_agent factory + recorder pluggable

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short  # tree limpio en development
docker compose ps   # api_dev/postgres/client_dev healthy
.venv/bin/python -c "import deepeval; print(deepeval.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
```

Si algo falla → resolver infra primero, NO arrancar TP.

## Patrón llamada API + SQL probes

Curl pattern:
```bash
TOKEN=$(.venv/bin/python scripts/get_clerk_test_token.py)
curl -sS -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 9ba0b29a-8507-424f-a48a-896f93218a25" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"<test>","conversation_id":null}'
```

DB: `docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "..."`

SQL probes en `01-tooling.md §Infraestructura interna`.

## Anomalías heredadas (de TP{N})

{Listar las anomalías que TP{N} detectó pero NO fixeó (excepción §4.4 documentada). Si TP{N} cerró todo verde, omitir esta sección.}

## Aprendizajes accionables de TP{N}

{1-3 bullets del §Aprendizajes para TP{N+1} de arriba. Copiar literal — el usuario ya leyó el reporte completo, no repetir narrativa.}

## Reglas non-negotiables

1. 5 ejes por escenario (flujo/calidad/tokens/latencia/UX). Sin los 5, escenario NO se cierra.
2. Root cause obligatorio — `# noqa` / `pytest.skip` / `assert True` / mock-tape-error PROHIBIDO.
3. NO diferir fixes — bug detectado durante TP se arregla en TP. TDD: test regresión RED → fix → GREEN.
4. TP termina verde — último OK = redesign funcionando.
5. Spanish neutro LatAm (regla 11) en cualquier user-facing tocado.
6. Native dev tools — lint/tests/eval WSL nativo, NUNCA `docker exec`.
7. Stage por nombre en commits (parallel-safety).

## Output esperado al cerrar

1. `docs/domains/copilot/testing-2026-04/results/TP{N+1}-{YYYY-MM-DD}.md` (template `04-protocol.md §Paso 6`).
   Incluir secciones **§Aprendizajes para TP{N+2}** + **§Prompt para TP{N+2}** (Anexo A).
2. Si `phases/TP{N+1}-*.md` cambió → commit incluido.
3. Commits conventional + push a `origin/development`.
4. Reporte al user: 3 líneas resumen + path al `results/`.

## Anti-patrones (no caer)

- Reportar "todo pasa" sin números.
- Saltar pre-research.
- Mockear LLM cuando TP exige real-LLM.
- Cerrar TP con fail abierto sin fix.
- Spawnear sub-agentes para escenarios paralelos (cada TP necesita context completo + iteración fix).
- Llenar reporte con info no accionable.
- Generar prompt TP{N+2} genérico sin adaptarlo (misión + research mandate + anomalías heredadas son específicos del TP{N+1}).

## Si te trabás

- No reproducís → SQL `copilot_trace_event WHERE turn_id=...` (`01-tooling.md`).
- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```

### Reglas de adaptación del template

Cada TP{N} adapta el template para TP{N+1} sustituyendo:

| Placeholder | Cómo se llena |
|---|---|
| Misión | Copia 1-3 líneas de `phases/TP{N+1}-*.md §Misión` |
| Research mandate | Apunta a `phases/TP{N+1}-*.md §Research mandate` (no copiar — referencia) |
| Anomalías heredadas | Solo las que TP{N} NO fixeó (excepción §4.4). Si TP{N} cerró verde, omitir sección |
| Aprendizajes accionables | Copia literal de §Aprendizajes para TP{N+1} del propio reporte |
| Setup heredado | Mantener lista canónica + agregar lo NUEVO que TP{N} introdujo (e.g. nueva fixture en conftest, nuevo script en `scripts/`) |

**Prohibido:** generar el prompt sin abrir `phases/TP{N+1}-*.md`. La misión y research mandate son específicos del TP siguiente, no genéricos.
