# PR-4 — Update Agents/Skills/Rules con Default-Flip Audit

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-4-update-agents-skills-default-flip-audit |
| Sprint padre | S1-test-integrity-and-coverage |
| PI padre | PI-11-backend-quality-guardrails |
| Estado | **shipped (2026-05-04)** |
| Tipo | meta-process update |
| Esfuerzo | M |
| Owner PM | /pm (PM directo, no builder técnico) |
| Claimed by session | — |
| Created | 2026-05-04 |

## Problema

PR-3 cementa regla `.claude/rules/anti-default-flip-audit.md` + arch fitness test. Sin PR-4 los agents/skills NO internalizan la regla:
- `nicolify-architect` no agrega bloque "Tests audit" en CONTRACT.md cuando propone flip
- `nicolify-backend` / `nicolify-agentic` no hacen Step 0 grep tests path viejo antes flip
- `nicolify-backend-auditor` no incluye Cat review "Default flip side-effect coverage"
- `pm` SKILL.md template PR.md no incluye bloque "Default flips audited"
- `.claude/rules/tdd-mandatory.md` no menciona patrón flag flips

Resultado sin PR-4: regla escrita en `.claude/rules/` pero defense-in-depth incompleta. Layer 5 (arch fitness) atrapa tests legacy mocks pero NO atrapa flips de **otras** flags side-effect (LITELLM_PROXY_ENABLED, futuras USE_DEEPAGENTS_*) en CONTRACT/code review.

## Outcome esperado

| Outcome | Métrica |
|---|---|
| `nicolify-architect` agent prompt | CONTRACT.md template incluye bloque "Tests audit" obligatorio cuando flip default detectado |
| `nicolify-backend` agent prompt | Step 0 default-flip detection (grep `core/config.py` defaults) + grep tests path viejo |
| `nicolify-agentic` agent prompt | Mismo Step 0 default-flip detection |
| `nicolify-backend-auditor` agent prompt | Nueva Cat review "Default flip side-effect coverage" |
| `nicolify-agentic-auditor` agent prompt | Misma Cat review |
| `pm` SKILL.md PR.md template | Bloque "Default flips audited" cuando aplique |
| `.claude/rules/tdd-mandatory.md` | Sección "Default flag flips" con regla |
| Process learnings updated | `docs/pm-nico/process/process-learnings.md` documenta caso PI-11 como anti-pattern referencia |

## Walking skeleton

PR-4 = PM directo (no builder técnico). PM lee + edita markdowns de:

### Step 1 — Update `.claude/agents/nicolify-architect.md`

Agregar al prompt template:

```markdown
## Default-flip audit (cuando CONTRACT propone flip)

Si CONTRACT.md propone flipear un default de feature flag (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*`, etc.) que cambia call path side-effect (events, persistence, logging, observability, LLM provider routing) → **OBLIGATORIO** incluir sección:

### § X Tests audit (default flip)

| Field | Value |
|---|---|
| Flag | {nombre} |
| Old default | {True/False} |
| New default | {True/False} |
| Side-effect path old | {path canónico viejo, ej. LegacyEventBus.publish} |
| Side-effect path new | {path canónico nuevo, ej. adapter_bus → outbox table} |
| Tests mockean path viejo | {grep result count + lista paths} |
| Migration strategy per test | {tabla path-by-path con estrategia: adapter_bus mock / outbox table probe / bypass capability} |
| Run with both flag values | {sí/no — required: sí pre-merge} |
| Commit body docs | {qué incluir en commit body para enforcement} |

Ver `.claude/rules/anti-default-flip-audit.md`.
```

### Step 2 — Update `.claude/agents/nicolify-backend.md`

Agregar a Step 0 GATE:

```markdown
### Step 0.5 — Default-flip detection (PR-3 anti-default-flip)

Si tu cambio toca `backend/src/core/config.py` defaults Y la flag controla call path side-effect (events, persistence, logging, observability, LLM routing):

1. Grep tests que mockean path viejo:
   ```bash
   grep -rn "<old_path>\|<old_class>\.<old_method>" /home/chris/AISALESHT/backend/tests/ 2>/dev/null
   ```
2. Si grep encuentra tests → STOP. Append IMPL-LOG sección "Default-flip pre-audit". Migrar mocks al path nuevo SOLO después CONTRACT confirma estrategia (§ Tests audit).
3. Run full suite con AMBOS valores flag pre-push:
   - `USE_<FLAG>=false .venv/bin/pytest ...`
   - `USE_<FLAG>=true .venv/bin/pytest ...`
4. Commit body include: "Flag <X> flipped Y→Z. Tests audited: N migrated, M bypass for legacy capability."

Ver `.claude/rules/anti-default-flip-audit.md`.
```

### Step 3 — Update `.claude/agents/nicolify-agentic.md`

Mismo bloque que Step 2, adaptado a context agentic (sales_agent + copilot defaults).

### Step 4 — Update `.claude/agents/nicolify-backend-auditor.md`

Agregar nueva categoría review:

```markdown
### Cat 14 — Default flip side-effect coverage

Verifica:
- [ ] PR diff toca `core/config.py` defaults? Si NO → cat NA, skip.
- [ ] Si SÍ → CONTRACT.md tiene § Tests audit (default flip) completo?
- [ ] Builder IMPL-LOG documenta grep tests path viejo + migration list?
- [ ] Commit body incluye "Flag X flipped Y→Z + Tests audited"?
- [ ] Suite corrió con ambos valores flag pre-push (gate-runner output)?
- [ ] `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` (o equivalente para otra flag) PASS?

Verdict:
- FAIL: flip sin § Tests audit + sin grep IMPL-LOG + sin commit body docs
- WARN: § Tests audit incompleto · ambos valores flag no corridos
- info: cleanup wording

Referencias:
- `.claude/rules/anti-default-flip-audit.md`
- `docs/pm-nico/pis/archive/PI-11-backend-quality-guardrails/retro.md` (caso origen)
```

### Step 5 — Update `.claude/agents/nicolify-agentic-auditor.md`

Mismo Cat review (numerar según schema agentic, ej. Cat 13).

### Step 6 — Update `.claude/skills/pm/SKILL.md`

Agregar a PR.md template (sección dedicada):

```markdown
## Default flips audited (cuando aplique)

Si PR propone flipear default flag side-effect, completar:

| Field | Value |
|---|---|
| Flag | {nombre} |
| Old default | {} |
| New default | {} |
| Side-effect path | {old → new} |
| Tests pre-audit grep | {count + lista} |
| Migration strategy | {ver CONTRACT § X Tests audit} |
| Both values runs | {sí/no} |
| Arch fitness coverage | {test_name si existe; CREATE si flag nueva} |

Si NO aplica: marcar `[x] No aplica — PR no flipea defaults side-effect`.
```

Y a sección "Antipatterns":

```markdown
- ❌ PR.md sin bloque "Default flips audited" cuando diff toca `core/config.py` defaults — auditor Cat 14 FAIL automatic
```

### Step 7 — Update `.claude/rules/tdd-mandatory.md`

Append sección:

```markdown
## Default flag flips (origen PI-11 2026-05-04)

Cuando flipeás default de feature flag side-effect (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, etc.) → TDD NO basta. **OBLIGATORIO** workflow extra:

1. Tests pre-flip: grep tests mockean path viejo, listar
2. Tests RED migración: adaptar tests AL PATH NUEVO antes flip
3. Run suite con AMBOS valores flag (RED en path viejo confirma migración necesaria; GREEN en path nuevo confirma migración correcta)
4. Tests GREEN flip: mergeable cuando ambos paths verde
5. Documentar en commit body

Sin estos pasos: tests siguen probando path muerto. Producción rompe silenciosa (path nuevo nunca probado real).

Ver `.claude/rules/anti-default-flip-audit.md`.
```

### Step 8 — Update `docs/pm-nico/process/process-learnings.md`

Append entry:

```markdown
## 2026-05-04 — Default flag flip = side-effect call path change (PI-11 origen)

**Caso:** commit `64738354` (PR-1 Sub-E PI-2) flipeó `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy `LegacyEventBus.publish` → 25 BE failures + polluter snapshot test no identificable + 80min hunt agente sin resolver durante `/pase-produccion` 2026-05-04.

**Anti-pattern detectado:** flipear default de flag que controla call path side-effect (events, persistence, logging, LLM routing) sin:
- Grep tests mockean path viejo
- Migrar mocks al path nuevo
- Run suite con ambos valores
- Documentar commit body

**Defense-in-depth cementado (PR-3 + PR-4):**
- Layer 1 PM PR.md template "Default flips audited"
- Layer 2 architect CONTRACT.md § Tests audit obligatorio
- Layer 3 builder Step 0.5 grep + migration strategy
- Layer 4 auditor Cat review "Default flip side-effect coverage"
- Layer 5 arch fitness test bloqueador (`test_no_legacy_eventbus_mock_when_outbox_on.py` + futuros)
- Layer 6 TDD rule sección "Default flag flips"

**Costo evitado por defense-in-depth:** ~3h sesión + 80min polluter hunt + 500k tokens × N futuros flags side-effect que se flipearán sin guardrail.

**Referencias:** `.claude/rules/anti-default-flip-audit.md`, `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`, `docs/pm-nico/pis/archive/PI-11-backend-quality-guardrails/retro.md`.
```

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Solo PR-3 (rule + arch fitness) sin update agentes | Mínimo blast radius | Defense-in-depth incompleta; agents/auditors no internalizan; otros flags no cubiertos arch fitness | descartada |
| B — PR-3 + PR-4 PM directo (markdown updates) | Defense-in-depth full; cobertura agents/auditor/skills/rules | Scope coordinado | **ELEGIDA** |
| C — PR-4 con builder técnico | — | Builder técnico innecesario para markdown edits | descartada — overhead spawn |

## Validación técnica preliminar

- Files afectados: 8 markdowns (.claude/agents/* x5, .claude/skills/pm/SKILL.md, .claude/rules/tdd-mandatory.md, docs/pm-nico/process/process-learnings.md)
- Blockers: PR-3 shipped (regla existe + arch fitness existe — referenciable)
- Tiempo estimado: PM directo ~1 ejecución (~30-60 min markdown edits + verify cross-references)

## Existing systems audit

| Sistema | Path | Decisión |
|---|---|---|
| `nicolify-architect` agent definition | `.claude/agents/nicolify-architect.md` | EXTEND con bloque default-flip |
| `nicolify-backend` agent definition | `.claude/agents/nicolify-backend.md` | EXTEND con Step 0.5 |
| `nicolify-agentic` agent definition | `.claude/agents/nicolify-agentic.md` | EXTEND con Step 0.5 |
| `nicolify-backend-auditor` agent definition | `.claude/agents/nicolify-backend-auditor.md` | EXTEND con Cat 14 |
| `nicolify-agentic-auditor` agent definition | `.claude/agents/nicolify-agentic-auditor.md` | EXTEND con Cat (numerar) |
| `pm` SKILL.md | `.claude/skills/pm/SKILL.md` | EXTEND PR.md template + antipatterns |
| `tdd-mandatory.md` | `.claude/rules/tdd-mandatory.md` | EXTEND sección "Default flag flips" |
| `process-learnings.md` | `docs/pm-nico/process/process-learnings.md` | APPEND entry 2026-05-04 |

## Decisiones diferidas

- ¿Numerar Cat agentic auditor 13 o usar otro número? (PR-4 PM decide al editar — consistencia con schema existente)
- ¿pr-folder-template/PR.md actualizar también con bloque "Default flips audited"? (Recomendado sí — PM decide al editar)

## Out of scope

- Modificar source code (PR-1 + PR-3 owns)
- Crear nuevos arch fitness tests para otras flags (incremental futuro post-PR-4)
- Update `claude-code-guide` agent o agentes externos no-Nicolify

## Copilot-first checklist

- [x] No aplica — meta-process.

## Agentes / skills recomendados

| Fase | Agente/skill | Modelo | Prompt | Entregable |
|---|---|---|---|---|
| Ejecución | `/pm` (PM directo, no builder técnico) | Opus | `prompts/01-pm-execute.md` | 8 markdowns updated |
| Verificación | `/pm` self-check | Opus | (parte de 01-pm-execute.md) | Cross-references valid + RESULT.md |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Agent definition | `.claude/agents/nicolify-architect.md` | EXTEND bloque default-flip CONTRACT |
| Agent definition | `.claude/agents/nicolify-backend.md` | EXTEND Step 0.5 grep tests path viejo |
| Agent definition | `.claude/agents/nicolify-agentic.md` | EXTEND Step 0.5 |
| Agent definition | `.claude/agents/nicolify-backend-auditor.md` | EXTEND Cat 14 |
| Agent definition | `.claude/agents/nicolify-agentic-auditor.md` | EXTEND Cat review |
| Skill | `.claude/skills/pm/SKILL.md` | EXTEND PR.md template + antipattern |
| Rule | `.claude/rules/tdd-mandatory.md` | EXTEND sección "Default flag flips" |
| Process | `docs/pm-nico/process/process-learnings.md` | APPEND entry 2026-05-04 |

## Tests requeridos (TDD)

- N/A — markdown edits.
- Validation: PM self-check cross-references válidos (links a `.claude/rules/anti-default-flip-audit.md`, `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`, PI-11 retro path post-archive).

## Aceptación

- [ ] 5 agent definitions updated
- [ ] `pm` SKILL.md updated con bloque PR.md template + antipattern
- [ ] `tdd-mandatory.md` updated con sección "Default flag flips"
- [ ] `process-learnings.md` appended entry 2026-05-04
- [ ] Cross-references válidos (links existen + paths reales)
- [ ] Antipatterns en `pm` SKILL.md mencionan "Default flips audited" missing
- [ ] `RESULT.md` PM
- [ ] Commit conventional `docs(meta): cement default-flip audit in agents/skills/rules`

## Riesgos

| Riesgo | Mitigación |
|---|---|
| PR-3 no shipped → cross-references rotos | PR-4 ship POST PR-3 PASS. PM verifica `.claude/rules/anti-default-flip-audit.md` exists + arch fitness test exists antes Step 1 ejecución |
| Agent definitions tienen estructura específica que PR-4 rompe | PM lee cada agent .md primero, identifica sección apropiada para extension, no reordena |
| Numbering Cat auditor inconsistente | PM lee schema existente (cat count actual) y agrega como next available number |
| pr-folder-template/PR.md también necesita update | PM evalúa al editar `pm` SKILL.md — si template necesita update, hace inline (parte mismo PR) |

## Notas operativas

- PR-4 = PM directo. NO spawn builder técnico.
- Ejecutar POST PR-3 ship (cross-references requieren `.claude/rules/anti-default-flip-audit.md` exist).
- 1 commit cohesivo `docs(meta): cement default-flip audit in agents/skills/rules` o granular si prefieres por surface.
