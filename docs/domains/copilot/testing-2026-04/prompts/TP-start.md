# Starter Prompt — Copilot Testing TP{N}

> Pegá este prompt en una conversación nueva de Claude Code, reemplazando `{N}` por el número de TP a ejecutar (0, 1, 2, …, 11). Indicá también si es la **primera corrida** del TP o una **iteración subsecuente** (porque la primera definió targets vs baseline).

---

# Iniciar TP{N} del Plan de Testing Copilot 2026-04

## Contexto (para vos)

Estás ejecutando el plan de testing del redesign Copilot 2026-04 (fases F0-F11 ya cerradas). El plan vive en `docs/domains/copilot/testing-2026-04/`. Tu trabajo es validar que las fases del redesign cumplen lo prometido a nivel **funcional + experiencial**, no solo a nivel de tests internos verde (que ya pasaron).

## Pre-lectura obligatoria (SIN esto NO arrancás)

Leé en este orden y entendé qué te toca antes de ejecutar:

1. `docs/domains/copilot/testing-2026-04/README.md`
2. `docs/domains/copilot/testing-2026-04/00-vision-and-coverage.md`
3. `docs/domains/copilot/testing-2026-04/01-tooling.md`
4. `docs/domains/copilot/testing-2026-04/02-test-plan.md`
5. `docs/domains/copilot/testing-2026-04/03-metrics-and-targets.md`
6. `docs/domains/copilot/testing-2026-04/04-protocol.md` — **el protocolo obligatorio**.
7. `docs/domains/copilot/testing-2026-04/phases/TP{N}-*.md` — TU fase.
8. Si hay `results/TP{N}-*.md` previos, leer el último (aprendizajes corrida anterior).
9. Fase del redesign que estás validando (mapeo en `02-test-plan.md`): `docs/domains/copilot/redesign-2026-04/learnings/F{X}-*.md`.
10. CLAUDE.md raíz + `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`.

## Misión TP{N}

(Esto se completa al pegar — describí brevemente: "validar TP1 routing+tier selection post-F11.1 wiring" o similar.)

## Reglas no negociables

1. **Pre-research fresco (PASO 2 del protocolo).** Mínimo 2 web searches del mandate del TP. Best practices abril 2026 cambian rápido — no asumas.
2. **5 ejes por escenario:** flujo / calidad / tokens / latencia / UX. NO se cierra escenario sin los 5.
3. **NO parchar.** Cualquier failure se diagnostica hasta root cause. Si fix excede scope, abrí plan separado en `results/`.
4. **Commit reporte final** en `results/TP{N}-{YYYY-MM-DD}.md` siguiendo template del protocolo.
5. **Spanish neutro LatAm** en cualquier output user-facing tocado (regla 11).
6. **Native dev tools** — lint/tests/eval WSL nativo, NUNCA `docker exec`.
7. **Stage por nombre** (parallel-safety) en cualquier commit.

## Pre-requisitos infra

Antes de arrancar:

- `git status --short` debe mostrar tree limpio en `development`.
- Containers up: `docker compose ps` muestra `visionarias_brain_dev`, `visionarias_postgres`, `visionarias_client_dev` healthy.
- DeepEval instalado: `cd backend && .venv/bin/python -c "import deepeval; print(deepeval.__version__)"` no falla.
- (Si TP UX) Chrome bridge funcionando: skill `chrome-devtools-verify` smoke check OK.
- Tenant de testing con data poblada según pre-req del TP (cada `phases/TP{N}-*.md` lista los suyos).

Si alguna falla → NO arranques el TP. Resolvé infra primero y reportá al user qué necesitás.

## Output esperado

Al cerrar la conversación dejás:

- `docs/domains/copilot/testing-2026-04/results/TP{N}-{fecha}.md` — reporte completo (template en `04-protocol.md §Paso 6`).
- (Si descubriste escenarios nuevos) `phases/TP{N}-*.md` actualizado.
- (Si aplicaste fixes) commits conventional con scope `test(copilot-tp{N}):` o `fix(copilot-{module}): … (TP{N})`.
- Push a `origin/development` (`parallel-safety` siempre).
- Reporte al user (resumen 3 líneas + path al `results/` + cualquier blocker / pregunta).

## Anti-patrones (te van a tentar — no caigas)

- **Reportar "todo pasa" sin números.** Cada eje pide número. Sin números el reporte es ruido.
- **Saltar el research** "porque ya sé el tool". Anti-pattern documentado en learnings F#.
- **Mockear el LLM cuando el TP exige real-LLM.** TP1 routing y TP9 deep-agent y TP11 UX necesitan medir cost/latency real, no stubs.
- **Cerrar TP con fail abierto sin plan.** Si no podés fixearlo en este TP, escribís el plan en `results/`. NO se cierra a ciegas.
- **Spawnear sub-agentes** para ejecutar TPs en paralelo. Cada TP necesita context completo + iteración fix. Los agentes pierden contexto.

## Si te trabás

- **No reproducís un escenario** → pegá el `turn_id` en `copilot_trace_event` query (template en `01-tooling.md`).
- **DeepEval falla raro** → versión specifica en `01-tooling.md`. Updates pueden romper API.
- **Chrome DevTools no conecta** → memory `feedback_chrome_devtools_verify_fe.md` (WSL2↔Windows bridge).
- **Cost te asusta** → `00-vision-and-coverage.md §5` proyecta ≤$0.30 corrida full.

---

**Primera tarea:** completá la pre-lectura del paso 1 + arrancá el pre-research del paso 2. Recién después de eso tocás algún tool.
