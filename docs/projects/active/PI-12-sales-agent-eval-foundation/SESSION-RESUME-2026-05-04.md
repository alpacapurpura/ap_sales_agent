# Session Resume — 2026-05-04

> Resume note para próxima sesión Claude Code. Esta sesión agotó contexto al 52%. Read THIS file FIRST en próxima sesión.

## Estado actual al cerrar

**Branch:** `development` (3 commits pushed a `origin/development`).

**Último commit:** `e7ea0394 feat(docs): map 16 modules → 52 capabilities + 94 stories + 4 gap reports`.

**PI activo:** PI-12 (`docs/projects/active/PI-12-sales-agent-eval-foundation/`).
**Phase:** `PLANNING`.
**Status:** `in-progress` esperando ratificación Chris.

## Qué se hizo en esta sesión

**Migración total a SDD Level 3 spec-driven harness.** 3 commits ya en remoto:

1. `64859048` foundation SDD (templates + rubrics + personas + 10 skills + 11 agents renamed + hooks + CLAUDE.md update)
2. `bc07b5c3` archive cleanup (12 carpetas legacy → `_archive/pre-sdd-2026-05-04/`)
3. `e7ea0394` mapping 16 módulos → 52 capabilities + 94 stories + 4 gap reports

Detalle completo en `docs/process/migration-plan.md` (todas las phases ✅).

## Qué quedó abierto (BLOQUEANTE)

PI-12 PI.md propuesto con:
- 3 objetivos (eval suite operacional, voice fidelity CI gate, cost tracking accuracy)
- 8 stories / 4 sprints / ~22d (ver tabla en `PI.md`)

**5 preguntas a Chris pendientes ratificación** (en `PI.md § Próximo paso` y `checkpoint.md § Decisiones pendientes`):

1. ¿Apruebas los 3 objetivos del PI?
2. ¿Apruebas decomposition en 8 stories / 4 sprints?
3. ¿Algún story que cambiar/agregar/quitar? (sugerí ej. `cost-budget-cap-eval-runs` para cap costo)
4. ¿Cambiar orden sprints? (sugerí cost-fix S→S1 quick win)
5. ¿Quién cura goldens dataset (S2 story 3)? Tenés 3 tenants reales o spawn agent helper?
6. ¿`backend/tests/agentic_evals/sales_agent/` confirmá path exacto?

## Bootstrap nueva sesión

```bash
# 1. Diagnóstico standard
git status --short && git branch --show-current && git log --oneline -3

# 2. Ver PI activo + checkpoint
cat docs/projects/active/PI-12-sales-agent-eval-foundation/checkpoint.md
cat docs/projects/active/PI-12-sales-agent-eval-foundation/PI.md

# 3. Si Chris ya respondió las 5 preguntas → /pm crea 8 stories/{id}/00-story.md + sprints/S1/sprint.md + handoff /po story 1
# 4. Si Chris NO respondió → preguntar las 5 preguntas (citá este archivo)
```

## Skills/agents disponibles (resumen)

**Skills nuevas activas** (paradigma SDD):
- `/pm` — director (rewrite, paradigma `docs/{product,projects,specs,process}/`)
- `/po` — spec gherkin AI-resistant
- `/ux-ui` — diseño UI + mockups
- `/ux-agentico` — flujo conversacional + state machine + slot architecture
- `/architect` — orchestrator (spawn `/architect-{be,fe,agentic}` paralelo)
- `/architect-{be,fe,agentic}` — sub-architects
- `/dev-team` — router qwen-opencode (BE/FE) vs Opus 4.7 (agentic OBLIGATORIO)
- `/auditor` — review (spawn `auditor-{be,fe,agentic}`)

**Agents renamed** (`.claude/agents/`):
- architect-orchestrator, builder-{be,fe,agentic}, auditor-{be,fe,agentic}, context-builder, gate-runner, grep-bot

**Hooks** (`.claude/hooks/`):
- post-edit-checkpoint.sh — auto-update last_modified
- pre-stop-verify.sh — warn dirty tree al cerrar

## Archivos críticos para próxima sesión leer

| Archivo | Qué tiene |
|---|---|
| `docs/process/migration-plan.md` | Status migración + hallazgos críticos consolidados (10 P0/P1 items) |
| `docs/projects/active/PI-12-sales-agent-eval-foundation/PI.md` | Scope PI-12 propuesto + 5 preguntas pendientes Chris |
| `docs/projects/active/PI-12-sales-agent-eval-foundation/checkpoint.md` | Resume protocol PI-level |
| `docs/process/gap-report-2026-05-04-group-c.md` | Gaps detallados sales_agent (origen PI-12) |
| `docs/product/modules/sales-agent.md` | Estado funcional sales_agent (frontmatter + capabilities) |
| `docs/product/stories/sales-agent/*.yaml` | 10 stories sales_agent ya mapeadas (las 6 agentic son target PI-12) |
| `docs/specs/templates/PI-template.md` + `sprint-template.md` + `story-{ui,agentic,service}.yaml` | Templates para crear nuevos artefactos |
| `docs/specs/personas/*.yaml` | 5 personas (lead-frio/tibio/caliente + tenant-novato/experto) |
| `docs/specs/rubrics/*.md` | 7 rubrics (voice-fidelity, no-hallucination, no-overpromise, tool-trajectory, empathy-tone, completeness, code-quality) |
| `CLAUDE.md` | Routing actualizado a SDD paradigm |

## Estructura `docs/` final

```
docs/
├── _archive/pre-sdd-2026-05-04/  ← histórico (12 carpetas obsoletas archivadas, preservadas)
├── domains/                      ← técnico SSoT por módulo (3MB)
├── etl/extraction-contract.md    ← auto-gen
├── guides/                       ← developer guides
├── pm-nico/                      ← LEGACY (PI-3..11 active terminan acá)
├── process/                      ← NUEVO (ticket-states, checkpoint-protocol, parallel-sessions, learnings, migration-plan, tech-debt/, gap-report-*.md)
├── product/                      ← NUEVO (INDEX, vision/roadmap/glossary, modules/, capabilities/, stories/, story-map/, opportunities/, ideas/)
├── projects/                     ← NUEVO (active/PI-12-.../, archive/)
├── references/                   ← refs externas
├── runbooks/                     ← ops
├── specs/                        ← NUEVO (INDEX, templates/, rubrics/, personas/)
└── stack-tecnologico.md
```

## Hallazgos críticos PI-12 contexto (de gap report group-c)

- `backend/tests/agentic_evals/sales_agent/` **NO EXISTE** → 6 agentic stories sin pass^k
- 5 personas + 7 rubrics declaradas pero **NO instrumentadas en CI**
- `cost_usd=0` post-fix por deepseek pricing mapping bug (provider=deepseek tagged como openai en `model_pricing_snapshot`)
- Voice fidelity threshold env `SALES_AGENT_VOICE_FIDELITY_THRESHOLD=0.7` declarada pero NO runs reales contra goldens
- Adversarial scenarios (jailbreak, prompt injection, persona hostile leak system prompt, cross-tenant tool args spoofing) **sin instrumentación**

## Multi-instancia

PI-12 marca `parallel_safe: false` (toca sales_agent — single session only durante el PI). Si otra sesión Claude tocaría sales_agent → STOP, escalar Chris.

## Próximo paso explícito (1 frase)

**Leer este archivo + `PI.md` → preguntar a Chris las 5 ratificaciones pendientes → crear 8 stories al recibir OK.**
