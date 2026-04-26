# Protocolo F-pos

Hereda íntegro `docs/domains/copilot/testing-2026-04/04-protocol.md`. Misma lógica research → execute → diagnose → fix → test → report → handoff. Diferencias específicas al FP work:

---

## Diferencias TP vs FP

### Paso 1 — Re-lectura de contexto

Cada FP arranca leyendo en este orden:

1. `docs/domains/copilot/fpos-2026-04/README.md`
2. `docs/domains/copilot/fpos-2026-04/02-fpos-plan.md` — DAG completo.
3. `docs/domains/copilot/fpos-2026-04/04-protocol.md` (este).
4. `docs/domains/copilot/fpos-2026-04/phases/FP{N}-*.md` — fase actual.
5. `docs/domains/copilot/fpos-2026-04/results/FP{N-1}-*.md` (si N≥2).
6. `docs/domains/copilot/testing-2026-04/results/TP11-2026-04-26.md` — origen del bug + aprendizajes plan padre.
7. `docs/domains/copilot/testing-2026-04/04-protocol.md` — protocolo padre integral.
8. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md` + `.claude/rules/backend-ddd.md` + `.claude/rules/frontend-fsd.md` (según capa stack del FP).
9. F# correspondiente del redesign si aplica (`docs/domains/copilot/redesign-2026-04/learnings/F{X}-*.md`).

---

### Paso 2 — Pre-research

Mínimo **2 web searches del Research mandate** del `phases/FP{N}-*.md`. Tessl tiles aplicables.

### Paso 3 — TaskCreate

Tasks granulares ≤2 horas. Por FP:
- 1 task por acceptance criterion.
- 1 task de TDD (test RED → GREEN).
- 1 task de live verification (re-run scenario que destapó bug).
- 1 task de regression suite.
- 1 task de results doc + commit + push + handoff.

### Paso 4 — Ejecución

Por cada acceptance criterion:

#### 4.1 Setup
- Containers up: `/dev-up` o `docker compose up -d`.
- Verify state actual del bug — reproducir el bug pre-fix con:
  - Test que falla (RED).
  - O scenario manual con SQL probe / Chrome DevTools que muestre síntoma.

#### 4.2 Run
Modo según FP:

| FP | Modo |
|---|---|
| FP1 | Mixto: TDD pytest + live Chrome DevTools (J1.click_apply re-run) |
| FP2 | TDD pytest + live (J2.T2 re-run "armame copy WhatsApp") |
| FP3 | TDD pytest + live + performance trace (TTFB measurement) |
| FP4 | TDD pytest (compliance test pattern) + live (J4 re-run audit) |

#### 4.3 Capturar evidence

**Before / After mandatory.** Sin both, AC no se cierra:

| Evidence | Cómo capturar |
|---|---|
| **Pre-fix síntoma** | Trace event SQL / DOM snapshot / screenshot / test RED. |
| **Post-fix closure** | Mismo prueba PASA / mismo scenario flow correcto / test GREEN. |
| **Tests added** | Snapshot del nuevo test que previene regresión. |
| **Latency / cost / metrics** | Solo si AC tiene métrica numérica (FP3 TTFB). |

#### 4.4 Diagnose + Fix

**Mismo `04-protocol.md §4.4` del plan padre.** Root cause obligatorio. Sin parchar.

TDD orden:
1. Test regresión RED (reproduce bug).
2. Fix arquitectónico GREEN.
3. Re-correr scenario live para validar.
4. Quality gates regresión (paso 5).

### Paso 5 — Quality gates

```bash
# Backend (siempre)
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q

# Frontend (FP1 only)
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
cd frontend && npx vitest run src/__tests__/architecture/
```

### Paso 6 — Reporte

`results/FP{N}-{YYYY-MM-DD}.md` con plantilla de `02-fpos-plan.md §Outputs`.

### Paso 7 — Actualizar `phases/FP{N}-*.md`

Si descubriste sub-bugs durante FP, agregar a sección "Sub-bugs descubiertos" del phase doc.

### Paso 8 — Commit + push

Conventional: `fix(copilot-fpos{N}): {scope corto} ({BugID})`. Stage por nombre.

### Paso 9 — Generar prompt FP{N+1} (excepto FP3 = último)

Template canónico igual a TP. Sustituir TP→FP. **Si FP{N} es el último (FP3 = cierre del batch), reemplazar handoff por sección "Cierre F-pos batch" con resumen agregado de los 4 FPs + recomendación de re-run TP11 selectivo.**

---

## Reglas anti-deriva (heredadas)

1. No agregar scope del FP fuera del bug específico. Si descubrís otro bug → al `results/` como recomendación, NO al código.
2. No skip pre-research.
3. No alucinar paths/símbolos.
4. No parchar — root cause obligatorio.
5. **TDD obligatorio** — test antes del fix.
6. El FP termina con código verde + AC cumplido + before/after evidence + tests passing.
7. Commit reportes en `results/`.
8. Cierre handoff obligatorio (excepto FP3 = último).

---

## Anexo A — Template canónico prompt FP{N+1}

```markdown
Iniciar FP{N+1} plan fpos-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión FP{N+1}

{1-3 líneas: qué bug cierra + qué confirma. Copiar de `phases/FP{N+1}-*.md §Misión`.}

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/fpos-2026-04/README.md`
2. `docs/domains/copilot/fpos-2026-04/02-fpos-plan.md`
3. `docs/domains/copilot/fpos-2026-04/04-protocol.md`
4. `docs/domains/copilot/fpos-2026-04/phases/FP{N+1}-*.md`
5. `docs/domains/copilot/fpos-2026-04/results/FP{N}-{fecha}.md` (aprendizajes corrida previa)
6. `docs/domains/copilot/testing-2026-04/results/TP11-2026-04-26.md` (origen bug)
7. `docs/domains/copilot/testing-2026-04/04-protocol.md` (protocolo padre)
8. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md`
9. Reglas relevantes según stack del FP (backend-ddd, frontend-fsd, etc).

## Pre-research obligatorio

Mínimo 2 web searches del Research mandate listado en `phases/FP{N+1}-*.md §Research mandate`. Tessl tiles según librerías.

## Setup heredado (NO rehacer)

- TP11 cerrado, B23-TP11 voseo system prompts fix vivo.
- Tenant test: visionarias-v4 `9ba0b29a-8507-424f-a48a-896f93218a25` (tenant_profile completo, brand_summary 0).
  - Si FP necesita brand_summary populated → tenant alpaca-2 `c67c9845-...` 580 chars v2 (pero tenant_profile vacío, redirect a onboarding).
- Sprint 0 routing: AGENT=Kimi K2.6 + REASONING=DeepSeek + NANO/FAST=OpenAI.
- deepagents 0.5.3.

## Pre-reqs infra (verificar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepagents; print(deepagents.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
curl -sS -o /dev/null -w "%{http_code}" http://localhost:3000
```

## Aprendizajes accionables de FP{N}

{Copia literal §Aprendizajes para FP{N+1} de results/FP{N}-*.md}

## Reglas non-negotiables

1. Acceptance criteria mandatorio (no scenarios+5 ejes — eso es TP).
2. TDD obligatorio: test RED → fix → GREEN.
3. Root cause obligatorio. NO parchar.
4. Before/After evidence en results.
5. Spanish neutro LatAm en cualquier user-facing tocado.
6. Native-first WSL, NUNCA `docker exec` lint/tests.
7. Stage por nombre commits.

## Output esperado al cerrar

1. `results/FP{N+1}-{fecha}.md` con before/after + AC checklist + métricas.
2. Si `phases/FP{N+1}-*.md` cambió → commit incluido.
3. Commits conventional + push origin/development.
4. Si N+1 < 4: generar `prompts/FP{N+2}-start.md`. Si N+1 = 3 (último FP): incluir §Cierre F-pos batch en results.
5. Reporte al user: 3 líneas resumen + path al `results/`.

## Anti-patrones

- Reportar AC sin evidence concreta.
- Mockear tests cuando AC pide live verification.
- Cerrar FP con sub-bug abierto sin TDD.
- Spawnear sub-agentes para AC paralelos (cada FP necesita context completo).

## Si te trabás

- Bug observability → fix recorder ANTES síntoma (`copilot-resilience.md`).
- Clerk token 401 → `.venv/bin/python scripts/get_clerk_test_token.py --no-cache`.
- Frontend 500 → `docker logs visionarias_client_dev | grep "Module not found"`.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```
