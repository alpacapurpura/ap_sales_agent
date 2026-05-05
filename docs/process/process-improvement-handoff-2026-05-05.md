# SDD Process Improvement — Handoff Doc

> **Origen:** sesión Chris + Claude Opus 4.7 del 2026-05-04 → 2026-05-05.  
> **Owner próxima sesión:** session nueva clean-context, leer este archivo PRIMERO + la sección "Mandatory reads" antes ejecutar.  
> **Goal:** implementar las 11 recomendaciones (R1..R11) que transforman 13 debilidades (D1..D13) del proceso SDD nivel 3 en oportunidades de mejora. Plus investigar mejoras adicionales.

---

## TL;DR

Sesión 2026-05-04/05 ejecutó pipeline completo `/po → /architect → /dev-team → /auditor` para PI-12 Sprint S1 (Story A `sales-agent-litellm-canonicalization` 11 tickets + Story B `sales-agent-eval-runner-foundation` 6 tickets). Completó **5/17 tickets** (T-1+T-2+T-7 Story A; T-1+T-2 Story B) — todos auditados APPROVED + pushed a `development`. Quedan **12 tickets pendientes** + **1 micro-ticket nuevo T-1-bis** (bug real T-1 follow-up). Análisis del proceso reveló 13 debilidades concretas → 11 recomendaciones priorizadas. Esta sesión nueva: **implementa R1-R4 (alto-ROI, antes seguir tickets) + investiga mejoras adicionales**.

---

## Mandatory reads (en orden)

1. **Este archivo** — completo, antes de cualquier cosa.
2. `docs/projects/active/PI-12-sales-agent-eval-foundation/PI.md` — contexto PI-12.
3. `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/sprint.md` — sprint S1.
4. `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/{01-spec.md,03-arch-be.md,04-tickets.yaml}` — Story A canonicalization (11 tickets, 5/17 totales).
5. `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-eval-runner-foundation/{01-spec.md,03-arch-be.md,03-arch-agentic.md,04-tickets.yaml}` — Story B eval-runner (6 tickets).
6. `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/06-audit/T-{1,2,7}-review.md` — auditor verdicts.
7. `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-eval-runner-foundation/06-audit/T-{1,2}-review.md` — auditor verdicts Story B.
8. `git log --oneline c2a1103a..HEAD` — todos los commits PI-12 S1 de la sesión origen.
9. `CLAUDE.md` + `AGENTS.md` + `.claude/rules/` — reglas vigentes (algunas mencionadas en R5+R8 son las que cambian).

---

## Estado git al cierre de sesión origen

```
49f6f68d docs(pi-12): T-2/T-7 audit reviews + Story B T-2 WARN self-fixes
6abfef7b feat(pi-12-T2-storyB): pytest fixtures + eval marker + langdetect
4a047d9d docs(pi-12-T2): record commit hash 8b6d798f in T-2 result frontmatter
8b6d798f feat(pi-12-T2): sync-pricing extends litellm_sync.py + Makefile target
38f7e1b7 test(pi-12-T7): migrate legacy adapter mocks → LiteLLM (anti-flip-audit Step 1+2 of 4)
d3be98f6 docs(pi-12-T1): auditor approves both Story A + Story B T-1
5856be4d feat(pi-12-T1): cost recorder LiteLLM canonicalization
52d58eaa docs(pi-12): add Story B 03-arch-agentic.md + finalize T-1 result hash
9ffae2ce feat(pi-12-T1-storyB): scaffold agentic eval harness dirs
8be8f575 docs(pi-12): architect plans S1 — litellm-canonicalization + eval-runner-foundation
c2a1103a feat(pi-12): ratify S1 specs — litellm-canonicalization + eval-runner-foundation
```

Branch: `development` (limpio + pushed). Sin WIP pendiente.

---

## Estado tickets PI-12 S1

```
Story A — sales-agent-litellm-canonicalization (11 tickets, Opus only)
├── T-1 cost recorder canonicalization     ✅ APPROVED merged
├── T-2 sync-pricing job                   ✅ APPROVED merged
├── T-3 migration repair                   ⏳ Pending — depende T-2
├── T-4 delete legacy adapters + gemini    ⏳ Pending — depende T-7
├── T-5 kill LITELLM_PROXY_ENABLED         ⏳ Pending — depende T-7
├── T-6a NULL tenant.{provider}_api_key    ⏳ Pending — depende T-5
├── T-6b verify gate (D8: 1d en vez 5d)    ⏳ Pending — depende T-6a
├── T-6c DROP COLUMN                       ⏳ Pending — depende T-6b
├── T-7 mock migration                     ✅ APPROVED merged
├── T-8 arch fitness update                ⏳ Pending — depende T-4+T-5
└── T-9 docs                               ⏳ Pending — depende T-8

Story B — sales-agent-eval-runner-foundation (6 tickets, Opus only)
├── T-1 scaffold dirs                      ✅ APPROVED merged
├── T-2 fixtures + langdetect              ✅ APPROVED merged
├── T-3 TrajectorySpy                      ⏳ Pending
├── T-4 multi-layer assertions             ⏳ Pending
├── T-5 smoke golden + tests               ⏳ Pending
└── T-6 Makefile + ops docs                ⏳ Pending

T-1-bis (NEW MICRO-TICKET) — cost_recorder fallback for custom yaml aliases
  Bug: litellm.get_llm_provider("kimi/kimi-k2.6") raises BadRequestError
       (LiteLLM upstream NO conoce "kimi" como provider — Nicolify lo define
       custom en litellm_config.yaml).
  Fix: en cost_recorder.py, si get_llm_provider() raises → fallback
       provider = model.split("/")[0].lower() if "/" in model else "unknown".
  Repro: cd backend && .venv/bin/pytest \
         tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py::TestUsageFallbacksFromResponseMetadata::test_response_metadata_token_usage_is_used \
         tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns
  → 2 fail con `cost_usd > 0` AssertionError.
  Recom: fold dentro T-3 Story A (migration repair) OR standalone hot-fix
         antes T-3 builder.
```

---

## Token consumption baseline (sesión 2026-05-04/05)

| Subagent type | Calls | Tokens (sum) | Tools (sum) | Avg/call |
|---|---|---|---|---|
| general-purpose (research) | 2 | 140k | 32 | 70k |
| general-purpose (po-spec) | 3 | 339k | 76 | 113k |
| Explore | 1 | 70k | 16 | 70k |
| architect-orchestrator | 2 | 479k | 77 | 239k |
| builder-backend (Opus) | 5 | 1241k | 467 | 248k |
| auditor-backend (Opus) | 5 | 769k | 162 | 154k |
| **Total subagentes** | **18** | **3038k** | **830** | **169k** |
| Main session | — | ~250k | — | — |
| **Gran total** | — | **~3.3M** | — | — |

**Para 5/17 tickets done.** Extrapolación lineal full PI-12 S1: ~10-12M tokens · ~$200-400 USD Opus 4.7. **Objetivo R1+R2 (context-builder + gate-runner): -30-40% → ahorro ~$60-150 por PI.**

---

## Las 13 Debilidades (D1..D13)

| ID | Debilidad | Impacto | Severidad |
|---|---|---|---|
| **D1** | Cada subagent re-lee spec+arch+rules desde cero | -30-40% tokens leídos repetidos | Alta |
| **D2** | Cada agent corre su propio pytest (no usa `gate-runner`) | Lint/test runs duplicados | Media |
| **D3** | Builder Story A T-1 corrió 133 tool uses + 305k tokens | 1 ticket ≈ $10-15 USD | Alta |
| **D4** | Auditor T-1 APPROVED pese a bug `kimi/kimi-k2.6 → BadRequestError` en cost_recorder | Bug llegó a S1 (T-1-bis nuevo) | **Crítica** |
| **D5** | WARN voseo + F632 cachados sólo en audit | Roundtrip extra fix | Media |
| **D6** | Schema-mirror exception (`modules/copilot/persistence/models/`) requiere juicio caso-a-caso | Auditor aprobó pero rule dice "NEVER touch" | Alta |
| **D7** | Folder rename Story A creó git status confuso | Tiempo debug | Baja |
| **D8** | T-6b operational gate **5 días** wall-clock pre-clientes | Sprint timeline 5x dev | Media |
| **D9** | Tickets T-1..T-9 nominales pero arch produjo 11 con T-6a/b/c | Confusión planeación | Baja |
| **D10** | Decisiones ratificadas en `01-spec.md` block — builder lee pero NO valida explícitamente | Risk: decisión ignorada | Media |
| **D11** | NO context-builder usado en ninguna fase | Ver D1 | Alta |
| **D12** | builder-agentic NUNCA invocado pese a Story B siendo agentic-adjacent | Posible bypass de hard rule | Media |
| **D13** | Subagentes spawn autoredacta result.md — duplicación format con template | ~5-10% tokens duplicados writing | Baja |

---

## Las 11 Recomendaciones (R1..R11) priorizadas

### Alto ROI (HAZ ESTAS PRIMERO en sesión nueva)

| R | Cambio | Esfuerzo | Beneficio | Resuelve |
|---|---|---|---|---|
| **R1** | **Phase 0 context-builder Haiku obligatorio** antes builder/auditor: produce `CONTEXT-BRIEF.md` 3-5k tokens summarizando spec + arch + rules + relevant code paths. Builder/auditor lee brief, NO docs raw. | 1h una vez (template + prompt update agentes builder-backend, auditor-backend) | -30-40% tokens (~$60-150 ahorro/PI) | D1, D11 |
| **R2** | **gate-runner Haiku post-builder** + JSON consumption por auditor. `gate-runner` ya está definido como subagent type pero NO usado. Cada builder al terminar invoca gate-runner que escribe `gate-output.json`. Auditor consume JSON, no raw logs. | 1h una vez (template prompt builder + auditor) | -10-15% tokens auditor | D2 |
| **R3** | **Auditor downstream regression scope** explícito. Tras T-N audit, auditor MUST run downstream tests que tocan shared surfaces afectados por T-N. Caso D4: T-1 cost_recorder afecta `modules/{copilot,sales_agent}/observability/test_callback_handler*.py` — auditor debió correrlas. Reglar en prompt template auditor-backend. | 30min cambio prompt | Atrapa bugs cross-surface temprano | D4 (CRÍTICO) |
| **R4** | **Pre-commit spanish-text regex + ruff F632** corre en builder phase, no audit phase. Hook captura voseo + identity comparison antes commit. | 30min (extender pre-commit hook + .githooks) | Cero WARN trivial en audit | D5 |

### Medio ROI (después de R1-R4)

| R | Cambio | Esfuerzo | Resuelve |
|---|---|---|---|
| **R5** | Codify schema-mirror exception en `.claude/rules/backend-ddd.md` — builder-backend may touch `modules/{copilot,sales_agent}/persistence/models/` purely for schema consistency con `shared/` migration. Cero juicio auditor caso-a-caso. | 15min | D6 |
| **R6** | **Decisions injection en `04-tickets.yaml`** ticket-level `decisions_applicable: [A1, A5, X2]` field + commit body MUST list how each was honored. Tighter compliance. | 1h template change | D10 |
| **R7** | T-6b operational gate **5d → 1d** para pre-clientes. Re-escalable a 5d cuando hay clientes. | Doc change único en arch-be.md Story A | D8 |
| **R8** | Sub-ticket numbering convention strict: T-{N}.a/b/c (no T-Na T-Nb), renumeración prohibida post-architect. | Doc change `docs/specs/templates/04-tickets-template.yaml` | D9 |
| **R9** | Single `git mv` commit BEFORE scope expansion, separado del scope-expansion commit. Cleaner history. | Doc change `pm` skill / `po` skill | D7 |

### Estructural (PI-13+)

| R | Cambio | Esfuerzo | Resuelve |
|---|---|---|---|
| **R10** | Result.md → JSON estructurado parser-friendly + render markdown derivado. | Refactor template + tooling | D13 |
| **R11** | Token budget cap explícito por subagent type (builder ≤ 200k, auditor ≤ 100k). Force agente eficiente. Plus builder-agentic vs builder-backend boundary clarification (audit existing tickets en backlog). | Prompt template change + audit pass | D3, D12 |

---

## Investigación adicional pedida (objetivo sesión nueva)

Chris quiere que la sesión nueva no sólo implemente R1-R11 sino también **investigue más posibles mejoras**. Áreas sugeridas para explorar:

1. **Métricas observables del proceso** — ¿podemos instrumentar el pipeline `/po → /architect → /dev-team → /auditor` con métricas (tokens consumidos, tools usados, time-to-merge, defect rate, rework rate)? Nice-to-have: tabla `process_run_metrics` o similar.
2. **A/B test de prompts** — comparar 2 versiones de prompt builder-backend (con context-builder vs sin) en el mismo ticket. Medir tokens + tiempo + verdict auditor.
3. **Auto-detección de duplicate work** — si 2 builders en paralelo van a tocar mismo archivo, alertar antes spawning. Pre-flight collision detection.
4. **Skill consolidation** — proyecto tiene 50+ skills. ¿Cuáles realmente se usan? ¿Cuáles son redundantes? Mapping uso real ↔ definición.
5. **Memoria de patterns** — repositorio de patterns aprendidos (ej. "fixture lazy import to keep collection cheap" — patrón usado 3x esta sesión). Skill que los devuelve cuando builder pregunta.
6. **Auditor self-improvement** — el auditor aprueba con WARN; ¿cómo mejorar para que catch críticos como D4 antes? Posible: regression test scope estándar para cada surface.
7. **Estimaciones architect vs realidad** — architect estimó 5h para T-1; el builder gastó ~1h dev wall pero 305k tokens. ¿Cómo afinar estimaciones con data real?
8. **Multi-tenant testing strategy** — Story B harness usa Visionarias real. ¿Necesitamos seed multi-tenant para Story 5 (3 tenants dataset)? Plan?
9. **Cost tracking del proceso mismo** — registrar tokens por phase en cada PI para benchmark. Tabla `pi_phase_token_usage`.
10. **Skill-vs-subagent decision tree** — cuándo invocar Skill (in main context) vs spawn subagent. Heurística clara.

---

## Plan recomendado para sesión nueva

### Fase 1 — Setup (15 min)
1. Leer este archivo + Mandatory reads.
2. Confirmar estado git limpio (`git status`).
3. Confirmar branch `development`.

### Fase 2 — Implementar R1-R4 (alto ROI, 3-4h estimado)

**R1 — Context-builder integration:**
- Editar prompt templates de `builder-backend`, `builder-agentic`, `auditor-backend`, `auditor-agentic` (en `.claude/agents/` o donde estén definidos).
- Insertar Phase 0: spawn `context-builder` Haiku con story-id → escribe `docs/projects/active/PI-{N}/sprints/SN/stories/{id}/CONTEXT-BRIEF.md` (3-5k tokens).
- Builder/auditor lee CONTEXT-BRIEF.md INSTEAD de spec+arch+rules+code paths raw.
- Test: spawn builder con un ticket trivial (T-1-bis sería buen test case).

**R2 — gate-runner integration:**
- Editar prompt builder-backend: post-implementation, spawn `gate-runner` Haiku con scope=`tests/shared/agent_observability/cost/` (o lo que aplique al ticket) → produce `gate-output.json`.
- Editar prompt auditor-backend: leer `gate-output.json` first, no re-correr `pytest` salvo regression cross-surface (R3).

**R3 — Auditor downstream regression scope:**
- Editar prompt auditor-backend: agregar Step "downstream regression". Cada cambio en `shared/` → auditor MUST run tests `modules/{copilot,sales_agent}/`. Cada cambio en `modules/X/` → auditor MUST run dependent modules tests.
- Definir mapeo `surface → downstream_test_targets` en CLAUDE.md o nueva regla.

**R4 — Pre-commit hooks expansion:**
- Editar `.git/hooks/pre-commit` o equivalente: agregar regex voseo + ruff F632 + ruff format check.
- Test: intentar commit con voseo → debe fallar.

### Fase 3 — Implementar R5-R9 (medio ROI, 2h estimado)
- Cada uno doc/template change. Listar como subtarea.

### Fase 4 — Investigación adicional (open-ended, 1-2h)
- Elegir 2-3 de las 10 áreas sugeridas para investigar.
- Producir `docs/process/process-improvements-2026-05-05-investigation.md` con findings + new recommendations R12+.

### Fase 5 — Cierre
- Update `docs/process/learnings.md` con esta iteración.
- Commit + push.
- Reportar Chris: qué se implementó, qué quedó, ROI esperado, próximos pasos.

---

## Constraints inmutables

- **Native-first** (no Docker para lint/tests).
- **Tenant isolation** en todo query.
- **Spanish neutro LatAm** en user-facing strings.
- **Conventional commits + sin force push + sin git pull** (parallel-safety.md).
- **Soft deletes**, **SQLA 2.0 async**, **structlog**, **Pydantic v2**.
- **TDD obligatorio** — RED antes GREEN.

---

## Output esperado de la sesión nueva

1. Pipeline integrado context-builder + gate-runner (R1+R2) verificado con test ticket T-1-bis.
2. Auditor mejorado con downstream regression (R3) — debe detectar el bug D4 si se reintroduce.
3. Pre-commit hooks ampliados (R4) — voseo + F632 + format.
4. R5-R9 docs change committed.
5. `docs/process/process-improvements-2026-05-05-investigation.md` con 2-3 áreas adicionales investigadas + R12+ recomendaciones.
6. Update `docs/process/learnings.md`.
7. Update `MEMORY.md` con references al nuevo proceso.
8. Reporte ejecutivo a Chris.

---

## Anti-patterns a evitar

- ❌ NO retomar tickets PI-12 S1 sin implementar R1-R4 primero (sería desperdicio token).
- ❌ NO hacer cambios en `04-tickets.yaml` Story A/B sin coordinar con T-1-bis decisión.
- ❌ NO modificar code de `modules/copilot/` o `modules/sales_agent/` salvo schema mirror (R5 codifica esa exception).
- ❌ NO eliminar `.claude/skills/dev-team/` o `pm/` o cualquier skill existente — pueden tener usos no auditados (R11 esto dejará para PI-13+).
- ❌ NO empezar T-3 Story A sin resolver T-1-bis primero (el bug bloquea consumer).

---

## Referencias clave (paths absolutos)

```
/home/chris/AISALESHT/docs/projects/active/PI-12-sales-agent-eval-foundation/
/home/chris/AISALESHT/docs/process/
/home/chris/AISALESHT/.claude/agents/  # subagent prompts
/home/chris/AISALESHT/.claude/rules/   # rules SSoT
/home/chris/AISALESHT/.claude/skills/  # skills SSoT
/home/chris/AISALESHT/CLAUDE.md
/home/chris/AISALESHT/AGENTS.md
/home/chris/.claude/projects/-home-chris-AISALESHT/memory/MEMORY.md
```

---

## Contacto

Si la sesión nueva tiene blocker o duda crítica → escalá a Chris (no tomes decisión de impacto sin ratificar). Toda decisión de scope debe ser ratificada por Chris (per `/po` skill rules).

Mismo principio que sesión origen: **robustness/escalabilidad > costo hoy**. No dejar deuda mañana.
