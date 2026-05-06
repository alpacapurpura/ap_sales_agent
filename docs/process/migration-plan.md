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
| 9 | Spawn 4 parallel mapping agents (16 modules → stories) | ✅ | 16 modules · 52 capabilities · 94 stories · 4 gap reports en `docs/process/gap-report-2026-05-04-group-{a,b,c,d}.md` |
| 10 | Hooks + CLAUDE.md/AGENTS.md update | ✅ | `.claude/hooks/*.sh` + root MDs |
| 11 | Commits + push | ✅ | 3 commits: `64859048` foundation · `bc07b5c3` archive cleanup · P9 mapping |

## Resultado final

- **`docs/`**: 27 carpetas → 11 vivas + 1 archive
- **52 capabilities** mapeadas
- **94 stories** YAML con scenarios AI-resistant (happy + negative + edge + adversarial)
- **4 gap reports** consolidan tests/coverage/eval suite gaps por grupo
- **10 skills nuevas** (`/pm` rewrite + `/po` `/ux-ui` `/ux-agentico` `/architect` `/architect-{be,fe,agentic}` `/dev-team` `/auditor`)
- **11 agents** renombrados al nuevo paradigma
- **2 hooks** auto-update checkpoint

## Hallazgos críticos cross-grupos (consolidados de 4 gap reports)

1. **CRÍTICO sales_agent**: NO existe `backend/tests/agentic_evals/sales_agent/`. 6 agentic stories sin pass^k tracking ni voice fidelity grader runs reales contra goldens.
2. **HIGH copilot**: eval suite parcial. Solo classifier+summarizer goldens. NO orchestrator-level (tool trajectory + voice fidelity + Card emission).
3. **Personas + Rubrics declaradas pero NO instrumentadas en CI** — son specs muertos hasta que un test runner los consuma.
4. **Cost tracking accuracy degraded sales_agent** — `cost_usd=0` por deepseek pricing mapping bug.
5. **Module doc drift advertising** — module-doc dice "placeholder" pero BE está implementado (3 services, 11 endpoints, 11 archivos test). Corregido.
6. **social_media BE realmente vacío** — capabilities cross-module via analytics + connections + assets + skill content-hunter.
7. **GA4 property picker FE PENDING** (Tasks 5-8).
8. **Watch channel renewal cron sin alert** — silent failure scheduling.
9. **campaigns**: copilot tools wiring (S3 PR-8) + ChannelRouter WhatsApp/Email (PI-2) pendientes.
10. **CRM copilot tools wrapping** candidato PI-3.

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
- `checkpoint.md` per story escrito y actualizado manualmente por el skill que cierra cada handoff (`/pm`, `/po`, `/po-ux`, `/architect`, `/dev-team`, `/auditor`). El hook `post-edit-checkpoint.sh` fue removido 2026-05-06 (lógica rota — ver `ticket-states.md` § Hooks).
