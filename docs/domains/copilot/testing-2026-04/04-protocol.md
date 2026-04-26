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

### 4.4 Diagnose si fail

Si el escenario falla en cualquier eje:

1. **NO comentar el test.** El fail es señal — perderla destruye el plan.
2. Abrir `copilot_trace_event` filtrado a este `turn_id` — buscar `event_type='error'` o tools que devolvieron status='error'.
3. Si no hay error explícito en trace → revisar `copilot_conversations.messages` (jsonb_pretty) para ver respuesta cruda del LLM.
4. Si tampoco aclara → `docker logs visionarias_brain_dev --tail 200 | grep -i error` para stack traces.
5. Identificar root cause:
   - **Bug arquitectónico** → fix architectural en `src/`. Test debe seguir esperando lo correcto, no lo bugueado.
   - **Test escenario mal diseñado** → corregir escenario en `phases/TP{N}-*.md`. Documentar por qué cambió.
   - **Regression vs F#** → cross-check con `learnings/F{X}-*.md`: si la fase prometía X y ya no entrega X, abrir bug en `docs/mejoras-proceso/to-do.md`.

**Prohibido absoluto:** parchar (`# noqa`, `pytest.skip`, `assert True`, mock que tape el error real).

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

## Paso 9 — Generar TP siguiente (opcional)

Si TP{N} bloqueaba a TP{N+1}, dejar `results/TP{N}-{fecha}.md` con sección final **"Listo para TP{N+1}"** + cualquier hook que aprendiste útil para la siguiente fase.

---

## Reglas anti-deriva (críticas)

1. **No agregar scope** del TP. Si descubrís oportunidad → al `results/` como recomendación, NO al código.
2. **No tocar §3 (lo que NO testeamos).** Si parece necesario → parar, preguntar al usuario.
3. **No alucinar.** Si no estás seguro de un path/símbolo → leer el archivo, no inventar.
4. **No skip pre-research.** Aunque "creas saber" — abril 2026, siempre algo cambió.
5. **No cerrar TP sin los 5 ejes** medidos por escenario.
6. **No tocar otros módulos sin que sigan funcionando** (regla redesign).
7. **No parchar.** Root cause o documentar plan separado.
8. **Commit reportes en `results/`** — los reportes son parte del producto del plan.
