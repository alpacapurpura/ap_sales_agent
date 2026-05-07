---
story_id: maintenance-skill-sales-agent-audit
type: service-story
subtype: maintenance
module: sales_agent
capability: null
po_version: 2
last_modified: 2026-05-06T19:30Z
ratified_by_chris: true
links:
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  skill_target: ../../../../.claude/skills/sales-agent-expert/
  related_rules:
    - ../../../../.claude/rules/sales-agent-brand-voice.md
    - ../../../../.claude/rules/anti-duplication.md
    - ../../../../.claude/rules/spanish-text.md
---

## Resumen ejecutivo

Auditar el skill SSoT `.claude/skills/sales-agent-expert/` (`SKILL.md` + 4 archivos `references/`) y aplicar diff que refleje la realidad del módulo `sales_agent` post homologación con `copilot` (mayo 2026). El audit no se limita a verificar paths citados — **evalúa la utilidad de cada sección/párrafo del skill y elimina o reestructura contenido obsoleto/redundante** (cero deuda técnica documental). El contenido eliminado se preserva verbatim en `T-1-impl-log.md` sección `Claims removed (archived)` para mantener trazabilidad histórica.

Salida: skill con paths/claims verificables 1:1 contra código vivo, surfaces compartidas (`shared/agent_observability/*`) explícitamente documentadas, zero contradicciones cross-archivo, y cero contenido sin propósito vivo. Esta story es PRE-REQUISITO ABSOLUTO de toda la sub-épica `eval-foundation-*`: si `/architect` y `/dev-team` leen un skill que miente o que tiene ruido obsoleto, contaminan downstream el diseño de tenant-seed/simulator/personas/goldens/graders.

**Outcome verificable:** (a) test pytest de regresión que recorre todo path/clase/módulo citado en el skill y asserta existencia (o presencia de marker `OBSOLETO:`), (b) `T-1-impl-log.md` con secciones `Claims removed (archived)`, `Claims updated`, `Claims added`, y `Utility verdicts` (una entrada por sección/párrafo del skill con verdict KEEP|UPDATE|DELETE|RESTRUCTURE + razón). El gate pasa GREEN al cierre de la story.

## Acceptance Criteria (Gherkin AI-resistant)

> 4 scenarios mínimos. Cada uno tiene grader explícito + path concreto.

### Scenario 1 — `audit-happy-path` (`type: happy`)

**Given:**
- HEAD limpio en branch `development`
- Skill en estado pre-audit: `.claude/skills/sales-agent-expert/SKILL.md` (188 líneas) + 4 archivos en `references/` (`conversation-stages.md`, `humanization-rules.md`, `sales-agent-brand-voice.md`, `tool-patterns.md`)
- Código vivo en `backend/src/modules/sales_agent/` + `backend/src/shared/agent_observability/` accesible read-only

**When:**
- /dev-team ejecuta el audit task siguiendo `05-guidelines.md` (que `/architect` producirá), 4 pasadas por el skill:
  1. **Pasada 1 — Verificación mecánica:** grep cada path/clase/símbolo citado en `SKILL.md` + `references/*.md` contra el repo
  2. **Pasada 2 — Surfaces compartidas:** scan `from src.shared.agent_observability` y similares desde `modules/sales_agent/**/*.py`, compara vs lo documentado en skill
  3. **Pasada 3 — Decisiones cardinales 60d:** consulta y cruza las 3 fuentes (`docs/process/learnings.md` últimos 60d con tag sales_agent/agent_observability, `git log --since="60 days ago"` sobre `modules/sales_agent/` + `shared/agent_observability/`, stories en `docs/archive/2026/stories/` con `module: sales_agent`); deduplica y resume en bullet list
  4. **Pasada 4 — Utility verdict por sección:** para CADA sección/párrafo de SKILL.md y de las 4 references emite verdict explícito (`KEEP` | `UPDATE` | `DELETE` | `RESTRUCTURE`) con razón citable (qué uso vivo justifica, o qué replacement existe)

**Then:**
- Skill tiene **0 paths citados que no existen sin marker `OBSOLETO:`** (assertion mecánica)
- Skill `SSoT vivos` table tiene cada concepto con path/símbolo verificable (greppable)
- `references/sales-agent-brand-voice.md` cita `personality_profiles.system_instruction` como SSoT y el path/columna existe en migrations + ORM model
- Sección **NEW** en SKILL.md "Surfaces compartidas con copilot (consumers shared/agent_observability)" lista cada subsystem que `sales_agent` consume con anchor a archivo concreto en `shared/`
- Sección **NEW** en SKILL.md "Decisiones cardinales últimos 60 días" referencia 2 stories shipped (`sales-agent-eval-runner-foundation`, `sales-agent-litellm-canonicalization`) + reframe synthetic-first 2026-05-06 + cualquier otra decisión emergida del cruce de las 3 fuentes
- Contenido con verdict `DELETE` o `RESTRUCTURE` se elimina/reorganiza en su archivo de origen y se preserva verbatim en `T-1-impl-log.md` sección `Claims removed (archived)` (cero pérdida de data — solo cero deuda técnica)
- `T-1-impl-log.md` documenta diff con 4 secciones obligatorias: `Claims removed (archived)`, `Claims updated`, `Claims added`, `Utility verdicts` (tabla con sección | archivo | verdict | razón)
- pytest de regresión `backend/tests/scripts/test_skill_sales_agent_audit.py` corre y pasa (todos los paths citados existen O tienen marker `OBSOLETO`)

**Graders:**
- `contract_test` — path: `backend/tests/scripts/test_skill_sales_agent_audit.py::test_skill_paths_resolve_or_have_obsolete_marker`
- `state_check` — target: filesystem; query: "every `path:` or fenced code-quoted symbol mentioned in `.claude/skills/sales-agent-expert/SKILL.md` o `references/*.md` resuelve a archivo/símbolo existente, salvo líneas con `OBSOLETO:` prefix"
- `state_check` — target: skill content; query: "SKILL.md contiene sección literal '## Surfaces compartidas con copilot' Y sección '## Decisiones cardinales últimos 60 días' (case-sensitive header)"
- `state_check` — target: filesystem; query: "`docs/product/stories/maintenance-skill-sales-agent-audit/T-1-impl-log.md` existe y contiene los 4 headers H3 `### Claims removed (archived)`, `### Claims updated`, `### Claims added`, `### Utility verdicts`"
- `state_check` — target: impl-log content; query: "tabla `### Utility verdicts` cubre 100% de secciones H2/H3 de SKILL.md + cada archivo en references/ (ningún parágrafo sin verdict)"

---

### Scenario 2 — `path-citado-no-existe` (`type: negative`)

**Given:**
- Skill `SKILL.md` cita un path/clase obsoleto, ejemplo: línea 38 menciona `agent_state_checkpoint` schema ó línea 91 cita `mv_daily_llm_cost_per_tenant_v2` que cambió de nombre/se eliminó
- Código vivo NO contiene ese path/clase

**When:**
- Auditor (humano o /dev-team) detecta el path obsoleto durante grep

**Then:**
- El path **NO se borra silenciosamente** del skill (preserva trazabilidad de decisión histórica)
- En su lugar, se prefija la línea con `OBSOLETO:` + comentario explicando el reemplazo (e.g., `OBSOLETO: mv_daily_llm_cost_per_tenant_v2 → renombrado a mv_daily_llm_cost_per_tenant_v3 en sales-agent-litellm-canonicalization 2026-05-06`)
- pytest de regresión interpreta `OBSOLETO:` como skip-allowed → test pasa GREEN para esa línea
- `T-1-impl-log.md` sección `Claims updated` registra la línea con before/after

**Graders:**
- `contract_test` — path: `backend/tests/scripts/test_skill_sales_agent_audit.py::test_obsolete_marker_skips_assertion`
- `state_check` — target: filesystem; query: "lines en SKILL.md o references/* que comienzan con `OBSOLETO:` están explícitamente documentadas en `T-1-impl-log.md` sección `Claims updated`"
- `state_check` — target: filesystem; query: "0 líneas con marker `OBSOLETO:` carecen de comentario inline post-marker (regex `OBSOLETO:[^—]*$` empty match)"

---

### Scenario 3 — `surface-compartida-no-documentada` (`type: edge`)

**Given:**
- Existe import desde `modules/sales_agent/` hacia `shared/agent_observability/X` (ejemplo: `BaseAgentCallbackHandler`, `FXResolver`, `pricing_resolver`, `format_for_channel`, `intent_detector`, `tenant_billing_config_repository`, `sanitize_payload`)
- Skill SKILL.md NO menciona ese subsystem en ninguna sección (`§0 Anti-duplication`, `§3 NO se toca`, `Decisiones cross-fase`, `SSoT vivos`, ó la nueva sección `Surfaces compartidas con copilot`)

**When:**
- Auditor escanea cross-codebase con `grep -rn "from src.shared.agent_observability" backend/src/modules/sales_agent/` y compara hits vs claims del skill

**Then:**
- Cada subsystem importado y NO documentado se **agrega** a la sección `Surfaces compartidas con copilot` con: path canónico shared, clase/función concreta consumida, archivo cliente sales_agent que lo consume
- Subsystem ya documentado pero con path stale → se actualiza
- `T-1-impl-log.md` sección `Claims added` registra cada nueva entry
- pytest enforcement: lista de subsystems shared consumidos == lista en sección skill (set equality)

**Graders:**
- `contract_test` — path: `backend/tests/scripts/test_skill_sales_agent_audit.py::test_shared_observability_consumers_documented`
- `state_check` — target: filesystem AST scan; query: "set of `shared.agent_observability.*` modules importados desde `modules/sales_agent/**/*.py` == set documentado en `## Surfaces compartidas con copilot`"
- `state_check` — target: skill content; query: "cada bullet en `## Surfaces compartidas con copilot` tiene formato `- shared.agent_observability.{subsystem} → consumed by modules/sales_agent/{file}` (regex strict)"

---

### Scenario 4 — `skill-self-contradicts` (`type: adversarial`)

> AI-resistant: detectar claims contradictorios cross-archivo dentro del skill mismo. Caso prioritario voseo (precedente alta señal: `.claude/rules/spanish-text.md` excluye sales_agent, `SKILL.md` decisión cross-fase línea 79 dice "voseo del tenant respetado", referencia `sales-agent-brand-voice.md` debe coincidir).

**Given:**
- Skill contiene 2+ archivos con claims sobre la misma invariante (ejemplos canónicos):
  - **Voseo:** `SKILL.md` decisiones cross-fase + `references/humanization-rules.md` + `references/sales-agent-brand-voice.md`
  - **Anti-duplication:** `SKILL.md` §0 + `.claude/rules/anti-duplication.md` (referenciado)
  - **Surfaces protegidas:** `SKILL.md` §3 vs decisiones cross-fase
  - **PII:** `SKILL.md` "PII regex sync — WONT-FIX" vs `references/sales-agent-brand-voice.md`
- Las 2+ ubicaciones afirman cosas distintas o incompatibles (ejemplo hipotético: SKILL.md dice "voseo respetado" y `humanization-rules.md` dice "evitar voseo en outputs")

**When:**
- Auditor scanea la matriz de claims cross-archivo durante el audit

**Then:**
- Cada contradicción detectada **bloquea el merge del audit** hasta resolución
- `T-1-impl-log.md` sección dedicada `## Contradictions detected` lista cada caso con: archivo A línea X, archivo B línea Y, claim A literal, claim B literal, resolución elegida + razón
- **Política de resolución híbrida** (ratificada Chris 2026-05-06):
  - **Auto-resolve dentro del skill** — si la contradicción es entre `SKILL.md` y un archivo de `references/*.md` del mismo skill, gana `SKILL.md` por design (la reference es derivada). El audit ajusta la reference y registra la resolución en impl-log.
  - **Escalar a Chris** — si la contradicción es (a) entre `SKILL.md` y un archivo `.claude/rules/*.md` externo, o (b) entre dos `references/*.md` del mismo skill sin que `SKILL.md` resuelva el caso, o (c) entre el skill y otro skill (`copilot-expert` u otros). El auditor pausa el merge y abre pregunta explícita en el output.
- Resolución NUNCA deja la contradicción viva — la regla de oro es "elimina o concilia, jamás coexisten"
- pytest `test_skill_no_self_contradiction` enumera al menos 4 invariantes canónicas (voseo, anti-duplication, §3 protected surfaces, PII regex stance) y asserta consistencia textual entre SKILL.md y reference files
- Caso adversarial sintético en el test: fixture inyecta string contradictorio en copia del skill → test debe detectarlo y fallar (proves grader funciona, no es no-op)

**Graders:**
- `contract_test` — path: `backend/tests/scripts/test_skill_sales_agent_audit.py::test_skill_no_self_contradiction`
- `contract_test` — path: `backend/tests/scripts/test_skill_sales_agent_audit.py::test_contradiction_detector_flags_synthetic_injection` (positive control — el test mismo se valida)
- `state_check` — target: filesystem; query: "si `T-1-impl-log.md` contiene sección `## Contradictions detected` con N>0 entries, cada entry resolved=true antes de marcar story como `developed`"

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Tiempo audit | Audit completable en ≤1d (5-6h efectivo build/dev-team — alcance expandido por Q4 utility audit) | story estimate vs git log |
| Determinismo | Test de regresión idempotente — corrida N veces post-audit, mismo resultado | `pytest --count=3` |
| Sin runtime impact | 0 cambios en `backend/src/modules/sales_agent/` ni `frontend/src/` | `git diff --stat` post-merge muestra 0 bytes en src/ |
| Cobertura paths | 100% paths citados en skill greppeables o marcados `OBSOLETO` | contract_test scenario 1 |
| Cobertura shared consumers | 100% imports `shared.agent_observability.*` documentados | contract_test scenario 3 |
| Cobertura utility verdict | 100% secciones H2/H3 de SKILL.md + 100% references files con verdict explícito KEEP/UPDATE/DELETE/RESTRUCTURE | state_check scenario 1 |
| Preservación de data | Contenido eliminado preservado verbatim en `T-1-impl-log.md::Claims removed (archived)` (cero pérdida histórica) | grep cross-check |
| Sin regresión harness | Tests existentes BE/FE/agentic verde post-merge | `make ci-parity` |
| Trazabilidad | Cada cambio en skill referenciado en `T-1-impl-log.md` con before/after | grep cross-check |
| i18n del audit | Skill mantiene Spanish neutro en frases nuevas (excepto cuando cita output del agente) | lint regex hook |
| Voseo magic comment | `references/humanization-rules.md` y `references/sales-agent-brand-voice.md` agregan `<!-- voseo-allowed -->` cuando citan voseo verbatim | pre-commit hook pasa |
| PII en log | `T-1-impl-log.md` no contiene secretos/tokens/PII | response_model análogo: revisar antes commit |

## Constraints técnicos heredados

- `.claude/rules/parallel-safety.md` — story corre en `development`, sin worktree; archivos del skill son SOLO de esta sesión durante el audit (M8: si otra sesión los toca, STOP)
- `.claude/rules/git-safety.md` — stage por nombre (`git add .claude/skills/sales-agent-expert/SKILL.md`), prohibido `git add -A`
- `.claude/rules/spanish-text.md` — magic comment `<!-- voseo-allowed -->` permitido en archivos del skill que documenten la excepción del agente (precedente: rules MD que citan glosario voseo verbatim)
- `.claude/rules/tdd-mandatory.md` — RED → GREEN: el test de regresión se escribe ANTES del primer cambio al skill (test corre RED contra el skill pre-audit por al menos 1 path obsoleto), luego cambios al skill lo llevan a GREEN
- `.claude/rules/anti-duplication.md` — el audit DEBE consumir esta rule como SSoT inventario shared, no re-redactar el inventario
- Native-first WSL: tests corren `cd backend && .venv/bin/pytest tests/scripts/test_skill_sales_agent_audit.py -v` (no Docker)

## Cross-module impact

- **Lee de:** `modules/sales_agent/`, `shared/agent_observability/`, `shared/billing/`, `shared/compliance/`, `shared/links/ports/`, `docs/process/learnings.md` (últimos 60d), `docs/archive/2026/legacy-pis/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md` (referenciado por skill línea 185)
- **Es leído por:** futuros invocadores del skill — `/architect`, `/architect-agentic`, `/dev-team`, `/auditor` (auditor-agentic), Chris en discovery, otros builders agentic
- **Eventos emitidos:** ninguno (cambio doc-only)
- **Eventos consumidos:** ninguno
- **Skill files tocados:** `SKILL.md` + las 4 references (`conversation-stages.md`, `humanization-rules.md`, `sales-agent-brand-voice.md`, `tool-patterns.md`)
- **Tests creados:** `backend/tests/scripts/test_skill_sales_agent_audit.py` (nuevo, ≥4 test functions)
- **Out of scope explícito:** NO tocar código del módulo `sales_agent`. NO tocar `copilot-expert` skill. NO tocar otros skills del repo.

## Decisions ratified (Chris 2026-05-06 v2)

- [x] **Q1 — Ubicación del test de regresión:** `backend/tests/scripts/test_skill_sales_agent_audit.py` (no arch fitness ratchet — el audit es evento puntual, no invariante estructural permanente).
- [x] **Q2 — Alcance "decisiones cardinales últimos 60 días":** las 3 fuentes (a) `docs/process/learnings.md`, (b) `git log --since="60 days ago"` sobre `modules/sales_agent/` + `shared/agent_observability/`, (c) `docs/archive/2026/stories/` con `module: sales_agent`. Cruzar y deduplicar; resultado vive como bullet list en SKILL.md sección nueva.
- [x] **Q3 — Política frente a contradicción detectada:** **híbrida** — auto-resolve dentro del skill (SKILL.md > references/), escalar a Chris si la contradicción es vs `.claude/rules/*.md` externo, vs otro skill, o si references/ se contradicen entre sí sin árbitro en SKILL.md. Detalle en Scenario 4.
- [x] **Q4 — `references/conversation-stages.md` y `references/tool-patterns.md`:** **in-scope FULL audit con utility verification** (alcance expandido vs v1). Carta libre para eliminar o reestructurar contenido obsoleto/redundante priorizando cero deuda técnica documental — pero **cero pérdida de data**: contenido eliminado se preserva verbatim en `T-1-impl-log.md::Claims removed (archived)`. El audit DEBE entender para qué sirve cada sección antes de decidir KEEP/UPDATE/DELETE/RESTRUCTURE; verdict + razón documentado en tabla `Utility verdicts` del impl-log.
- [x] **Q5 — Magic comment `voseo-allowed`:** sí, autorizado para `references/humanization-rules.md` y `references/sales-agent-brand-voice.md` cuando citen glosario voseo verbatim. Precedente: `.claude/rules/spanish-text.md` mismo lo usa.

## Próximo paso

`type=service-story` → skip UX → `/architect` directo cuando `ratified_by_chris=true`. /architect produce `03-arch.md` (decompose en sub-arq BE solo, no FE no agentic) + `04-validators.yaml` (los contract_test y state_check de arriba como must_pass:true) + `05-guidelines.md` (workflow del audit + anti-patterns) + `06-tickets.yaml` (probable T-1 único: write test RED → audit + apply diff → tests GREEN → impl-log).

## Changelog

- v1 2026-05-06 — /po draft inicial; 4 scenarios + 5 open questions; awaiting Chris ratification
- v2 2026-05-06 — Chris ratificó las 5 preguntas. Cambios: (Q1) tests en `tests/scripts/`, (Q2) las 3 fuentes para decisiones 60d, (Q3) política híbrida de resolución, (Q4) audit FULL con utility verdicts + permiso eliminar/reestructurar preservando data en impl-log, (Q5) magic comment voseo-allowed autorizado. Resumen ejecutivo + Scenario 1 (4 pasadas + tabla Utility verdicts) + Scenario 4 (política híbrida) + NFR (utility verdict coverage + preservación data + voseo magic comment) actualizados.
- v2 2026-05-06 19:30Z — **Chris ratified v2 final.** State transition refining → refined. Handoff a /architect.
