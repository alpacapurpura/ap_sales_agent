# Migration Plan — Spec-Driven Harness (SDD Level 3)

**Started:** 2026-05-04
**Status:** in-progress
**Mode:** Total reboot. `docs/pm-nico/` queda intact (legacy lectura manual). `docs/{product,projects,specs,process}/` es nuevo SSoT.

## Decisiones cardinales (commit 2026-05-04 con Chris)

1. **Migración paralela.** `docs/pm-nico/` queda intact. PIs activos (PI-3..11) cierran en estructura vieja. PI-12+ nace en nueva.
2. **Story atómica.** 1 story = 1 archivo YAML en `product/stories/{module}/{id}.yaml`. Capability = índice agregador.
3. **3 tipos story:** `ui-story` | `agentic-story` | `service-story`. Eval policy distinta cada uno.
4. **Scenarios AI-resistant.** `happy + negative + edge + adversarial` mínimo en cada story.
5. **Personas + Rubrics first-class** en `specs/{personas,rubrics}/`. Reusables.
6. **Tickets cross-stack split forzado.** Agentic ticket → Opus. BE/FE no-agentic → opencode/qwen. Prohibido mezclar en 1 ticket.
7. **PO+UX combinable mismo session** (loop iterativo). UX puede proponer `delta-spec.md`, /po ratifica.
8. **/pm habla solo NUEVO.** Chris pide manual cuando necesita revisar `pm-nico/`.
9. **Agents `nicolify-*` renombrados al nuevo paradigma.**
10. **Anti-teléfono-descompuesto** + `checkpoint.md` por nivel = resume protocol.

## Phase status

| # | Phase | Status | Artifact |
|---|---|---|---|
| 0 | Working plan | ✅ | `docs/process/migration-plan.md` |
| 1 | Framework dirs + INDEX | 🔄 | `docs/{product,projects,specs,process}/` |
| 2 | Templates | ⏳ | `docs/specs/templates/` |
| 3 | Rubrics | ⏳ | `docs/specs/rubrics/` |
| 4 | Personas | ⏳ | `docs/specs/personas/` |
| 5 | Process docs | ⏳ | `docs/process/{ticket-states,checkpoint-protocol,parallel-sessions-protocol}.md` |
| 6 | Migrate 16 current-state → product/modules | ⏳ | `docs/product/modules/*.md` |
| 7 | Rename 11 nicolify-* agents | ⏳ | `.claude/agents/{architect-orchestrator,builder-{be,fe,agentic},auditor-{be,fe,agentic},context-builder,gate-runner,grep-bot}.md` |
| 8 | Create 9 new skills | ⏳ | `.claude/skills/{pm,po,ux-ui,ux-agentico,architect,architect-{be,fe,agentic},dev-team,auditor}/SKILL.md` |
| 9 | Spawn 4 parallel mapping agents (16 modules → stories) | 🔄 | `docs/product/stories/{m}/*.yaml` + `docs/product/capabilities/{m}/*.yaml` + gap report |
| 10 | Hooks + CLAUDE.md/AGENTS.md update | ✅ | `.claude/hooks/*.sh` + root MDs |
| 11 | Commit foundation + P9 commit + summary | 🔄 | git log: `64859048` foundation. Pendiente P9 commit. |

## Resume protocol

Si esta sesión muere:
1. `cat docs/process/migration-plan.md` — leer phase status
2. Phase con `🔄` o último `⏳` previo `✅` = retomar ahí
3. Cada phase tiene artifact path → check existencia para validar avance real
4. `git status` para ver work-in-progress
5. Siguiente sesión actualiza esta tabla antes de proceder

## Mapeo agents nicolify-* → nuevo paradigma

| Viejo | Nuevo | Rol nuevo |
|---|---|---|
| nicolify-architect | architect-orchestrator | Wrapped por `/architect` skill |
| nicolify-backend | builder-backend | Invocado por `/dev-team` cuando ticket=BE no-agentic |
| nicolify-frontend | builder-frontend | Invocado por `/dev-team` cuando ticket=FE no-agentic |
| nicolify-agentic | builder-agentic | Invocado por `/dev-team` cuando ticket=agentic (Opus only) |
| nicolify-backend-auditor | auditor-backend | Invocado por `/auditor` |
| nicolify-frontend-auditor | auditor-frontend | Invocado por `/auditor` |
| nicolify-agentic-auditor | auditor-agentic | Invocado por `/auditor` |
| nicolify-context-builder | context-builder | Invocado por todos los skills (pre-flight) |
| nicolify-gate-runner | gate-runner | Invocado por `/dev-team` y `/auditor` |
| nicolify-grep-bot | grep-bot | Utility — invocado por cualquiera |
| nicolify-ux-designer | (deprecated) | Capacidades absorbidas por `/ux-ui` skill |
| nicolify-feature | (deprecated) | Reemplazado por flujo /po → /ux → /architect → /dev-team → /auditor |

## Skills nuevos vs existentes

**Nuevos** (a crear):
- `/po` — user story → spec gherkin AI-resistant
- `/ux-ui` — diseño UI desde spec (consolida ux-disruptivo+ux-flow-architect)
- `/ux-agentico` — diseño flujo conversacional
- `/architect` — orchestrator (spawn architect-{be,fe,agentic} en paralelo)
- `/architect-be` — sub-architect BE
- `/architect-fe` — sub-architect FE
- `/architect-agentic` — sub-architect agentic
- `/dev-team` — toma ticket, route a builder correcto (qwen vs opus)
- `/auditor` — review + tests + verdict pass/fail

**Reescritos:**
- `/pm` — orchestrator producto, solo nuevo paradigma

**Mantenidos sin cambio:**
- `/test-backend`, `/test-frontend`, `/test-all` — gates
- `/dev-up`, `/migrate` — infra
- `/cierra-limpio`, `/estado`, `/rescata` — workflow Chris
- `/pase-produccion` — deploy
- Domain experts (`brand-expert`, `offer-expert`, `sales-agent-expert`, `copilot-expert`, `metrics-expert`, `manychat-expert`, `content-hunter`, `data-storyteller`) — cargados por skills nuevos cuando aplique
- Tessl skills — sin cambio

**Deprecados** (eliminados o absorbidos):
- `nicolify-feature` — reemplazado por flujo
- `ux-disruptivo` + `ux-flow-architect` — absorbidos en `/ux-ui`
- `pm-nico` SSoT path — `pm` skill nuevo apunta a `docs/product/`+`docs/projects/`

## Notas críticas

- **NO renombrar archivos en `docs/pm-nico/`** durante migración. Queda intact.
- **NO tocar `pis/active/PI-3..11/`** — los builders activos terminan ahí.
- Cada agente nuevo o renombrado: `tools:` mínimas (Vercel principle).
- Cada skill carga ÚNICAMENTE sus refs cuando se invoca.
- `checkpoint.md` per nivel (PI/sprint/story) escrito por `/pm` y actualizado por hooks.
- Hooks `.claude/hooks/post-edit-checkpoint.sh` actualiza `last_artifact` automáticamente.
