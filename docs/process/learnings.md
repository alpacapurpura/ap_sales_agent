# Process Learnings (append-only)

> Owner: `/pm`. NUNCA editar entries históricas. Solo append.
> Cada incident / decisión cardinal / surprise / case study agrega entry.

---

## 2026-05-04 — Migración a SDD Level 3 / Spec-Driven Harness

**Contexto:** Estructura `docs/pm-nico/` se quedó corta. 6 PIs activos. Múltiples sesiones Claude. Necesidad de specs ejecutables + evals AI-resistant + resume protocol robusto.

**Decisiones:**
1. Estructura `docs/{product,projects,specs,process}/` paralela a `pm-nico/`. Migración gradual.
2. Story = unidad atómica. 1 archivo YAML. NO capability monolítico.
3. 3 tipos story: ui / agentic / service. Eval policy distinta.
4. Scenarios AI-resistant obligatorios: happy + negative + edge + adversarial.
5. Personas + Rubrics first-class versionados.
6. 9 skills nuevos: /pm rewrite, /po, /ux-ui, /ux-agentico, /architect (+ 3 sub), /dev-team, /auditor.
7. 11 nicolify-* agents renombrados al nuevo paradigma.
8. Tickets agentic = Opus 4.7 obligatorio (qwen ban).
9. Tickets BE/FE no-agentic = qwen-opencode preferido.
10. Self-fix auditor cap 2 iter, después escala.
11. /pm habla solo nuevo. Legacy `pm-nico/` lee on-demand manual.

**Fuentes consultadas:**
- Anthropic effective-harnesses-for-long-running-agents
- Anthropic harness-design-long-running-apps
- Anthropic multi-agent-research-system
- Anthropic managed-agents
- Anthropic AI-resistant-technical-evaluations
- Anthropic demystifying-evals-for-ai-agents
- Vercel "We removed 80% of our agents tools"
- τ-Bench / τ2-Bench (multi-turn evals)
- ejemplo-harness-subagentes (betta-tech)

**Riesgos identificados:**
- Migration parcial: durante 4-6 semanas, /pm habla solo nuevo pero PIs viejos siguen en pm-nico/. Chris debe pedir manual cuando query algo legacy.
- Aprendizaje curva: 9 skills nuevos. Primer story exemplar piloto crítico.
- Cost: multi-agent multiplica tokens (Anthropic 15x). Mitigación: solo orchestrator + sub-architects en Opus, devs en qwen/sonnet cuando posible.

---

## 2026-05-05 — Process improvement R1-R9 + A0 (post PI-12 S1 piloto)

**Contexto:** PI-12 S1 ejecutado pipeline completo `/po → /architect → /dev-team → /auditor` para 2 stories (litellm-canonicalization 11 tickets + eval-runner-foundation 6 tickets). Completó 5/17 tickets aprobados. Análisis post-mortem reveló 13 debilidades (D1-D13) → 11 recomendaciones (R1-R11). Sesión 2026-05-05 implementó R1-R9 + nueva A0 (hardening context-builder).

**Token baseline sesión origen (5 tickets):** ~3.3M tokens · ~$200-400 USD Opus 4.7. Extrapolación full S1: 10-12M tokens.

**Cambios cardinales (15 commits):**

A0 — Hardening context-builder Haiku (BLOCKER pre-R1, agregada por Chris durante session):
- H1-H10 implementadas: WebSearch+WebFetch+Tessl tool access, maxTurns 60→120, auto-keyword inference, cross-reference anti-duplication.md inventory, canonical docs URL fetch (15 frameworks), domain skill SKILL.md preload, validator pass adversarial probe (NEW agent context-validator), 3-state faithfulness flag (clean/partial/blocking), audit log mandatory, free-form pass §14, self-budget snapshot §16
- Sin hardening, context-builder = punto entrada frágil → R1 cementaba fragilidad
- Bug D4 caso: validador hubiera detectado missing test coverage cross-surface

R1 — context-builder Phase 0 en /dev-team + /auditor SKILL.md:
- Orchestrators ahora spawn context-builder Haiku antes builder/auditor
- Builder agents (BE/FE/agentic) consumen CONTEXT-BRIEF.md priority read
- Patched FE agents (builder-frontend + auditor-frontend) que NO referenciaban brief antes — parity catch-up
- Beneficio esperado: -30-40% tokens leídos repetidos

R2 — gate-runner enforcement orchestrator level:
- /dev-team Step 4 obliga gate-output.json existir + any_fail=false (force spawn si missing)
- /auditor Step 2 verifica fresh JSON (vs LATEST_COMMIT_TS) antes spawn sub-auditor
- Sub-auditor BLOCKED si gate-output.json shows fail (ticket vuelve dev-team)
- Beneficio: -10-15% tokens auditor + cero auditor inviste en código que falla gates

R3 — Auditor downstream regression scope (caso D4 CRÍTICO fix):
- Nuevo rule .claude/rules/auditor-downstream-regression.md (tabla SSoT 25 entries surface→downstream tests)
- auditor-{backend,agentic} agents agregan Step downstream_regression_scope MANDATORY post consume_gate_output
- Verdict math: downstream FAIL → overall FAIL Cat 10
- Sin esto repetimos D4 (cost_recorder approved pese a bug callback handlers cross-surface)

R4 — Pre-commit hook (voseo + ruff completo + format):
- scripts/git-hooks/pre-commit canonical SSoT (voseo regex + ruff check --no-cache + ruff format --check)
- .husky/{pre-commit,pre-push} wrappers exec scripts/git-hooks/* (husky 9.x compat)
- BUG PRE-EXISTING DESCUBIERTO + FIXED: pre-push hook DEAD desde install husky (core.hooksPath = .husky bypassea .git/hooks/pre-push) → ci-parity gate prod auto-deploy bypasseado silenciosamente. R4 wrapper resurrects gate.
- Voseo regex completo glosario spanish-text.md, exclude modules/sales_agent/ voice templates, magic comment voseo-allowed honor
- Tests verified: voseo MD blocked, ruff F632 blocked, clean pass

R5 — Schema-mirror exception codify backend-ddd.md:
- builder-backend MAY touch modules/{copilot,sales_agent}/persistence/models/ purely para schema mirror desde shared/ migration
- Cero juicio caso-a-caso auditor (caso PI-12 S1 T-1 ratificado por Chris ahora regla)
- Lista permitido (Mapped[] cols, indexes, FKs hacia shared, DEPRECATED markers) vs no permitido (touch domain/application/api/observability, change runtime, create table solo agentic)

R6 — Decisions injection 04-tickets template:
- Ticket-level field decisions_applicable: [D1, D3, X2] que lista decisions ratificadas upstream
- Builder commit body MUST cite cada D# en sección "Decisions honored"
- Auditor Cat 11 verifica cite — WARN si missing

R7 — T-6b operational gate 5d→1d (Story A pre-clientes):
- Editado 04-tickets.yaml + 03-arch-be.md Story A T-6b
- Sin tráfico productivo no justifica 5d wall-clock; re-escalable post-clientes activos

R8 — Sub-ticket numbering convention strict:
- T-{N}.a / T-{N}.b / T-{N}.c (con punto obligatorio)
- PROHIBIDO T-Na / T-Nb sin punto (origen confusión PI-12 Story A)
- Renumeración prohibida post-architect

R9 — Single git mv commit pre-scope-expansion (pm SKILL):
- Refactors estructurales = 2 commits separados
- Commit 1: git mv puro (zero content diff, git rename detection auto)
- Commit 2: scope expansion
- Cleaner history, bisect-friendly

Investigation phase produjo:
- docs/process/process-improvements-2026-05-05-investigation.md
- 4 áreas estudiadas: #1 metrics observables, #4 skill consolidation, #5 patterns memory, #6 auditor self-improvement
- 9 nuevas recomendaciones priorizadas R12-R20
- Cluster cohesivo PI-13: R12 + R14 + R16 + R18 (~15-25h, $TBD ROI)

**Lecciones aprendidas (cross-cutting):**

1. **"Punto entrada frágil cementa downstream rabbit hole"** — Chris pause R1 para hardening context-builder cuando se dio cuenta validador downstream era único safety. Lección: invest hardening upstream antes integrate downstream. Sin A0, R1 cementaba fragilidad.

2. **"Hooks invisibles bypasseados silenciosamente"** — pre-push DEAD descubierto incidentalmente al testear pre-commit. Lección: cuando merger tooling (husky 9 + .git/hooks legacy), explicit verify cada hook fires. R4 fix wrappers permite ambos paths funcionar.

3. **"Adversarial validator > checklist verifier"** — context-validator agent hace synonym scan + spot-check + blind audit en lugar de "verify each section is filled". Adversarial mode catch lo que builder MISSED, no confirma lo que tiene.

4. **"R3 mecánica > juicio auditor caso-a-caso"** — tabla SSoT `surface → downstream_test_targets` reemplaza decision-making per-PR. Mantenimiento manual cuando agregás surface shared/ cross-consumer pero amortiza muchos audits.

5. **"Decisions honored cite > confiar builder leyó spec"** — R6 forces explicit traceability. Sin cite → WARN. Pequeña fricción por cada commit (1 line) pero garantiza decisión NO ignorada silenciosamente (D10).

**Riesgos restantes:**

- **Métricas baseline missing:** R12 propone capture pero NO implementado. Validar R1-R9 ROI requiere medir antes/después. Próxima sesión: instrumentar antes spawning otra agent.
- **Skill consolidation deferred:** R14 propone audit pero 50+ skills siguen vigentes. Cognitive overhead persiste hasta PI-13.
- **Pattern-memory empty:** R16 skill diseñada pero patterns/ vacío. Sin seed inicial, skill returns nada útil.

**Fuentes consultadas:**

- docs/process/process-improvement-handoff-2026-05-05.md (handoff sesión anterior)
- bug D4 PI-12 S1 T-1 (cost_recorder canonicalization caso origen R3)
- pre-existing bug husky core.hooksPath ci-parity bypass (descubierto R4)

**Commits sesión:**
- 717123e5 feat(context-builder): harden Haiku pre-flight reader (H1-H10) + adversarial validator
- d276dce5 feat(dev-team,auditor): R1 integrate context-builder Phase 0 + FE agents parity
- e62919ac feat(dev-team,auditor): R2 enforce gate-runner usage at orchestrator level
- a12bf22d feat(auditor): R3 downstream regression scope rule + integrate auditor-{be,agentic}
- 19694702 feat(hooks): R4 voseo regex + ruff in pre-commit, fix dead pre-push under husky
- 1414563d docs(rules): R5 codify schema-mirror exception in backend-ddd.md
- ab56966e docs(templates): R6+R8 decisions injection + sub-ticket numbering convention
- 303a40a7 docs(pi-12-T6b): R7 operational gate 5d→1d pre-clientes
- 5808b7f3 docs(pm): R9 git mv aislado convention pre-scope-expansion
- 3d77e81b docs(process): investigation 4 áreas → R12-R20 priorizadas

---
