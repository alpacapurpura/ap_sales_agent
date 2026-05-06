---
name: po
description: "Product Owner Nicolify v4 (post pm-redesign 2026-05 Punto 4). SCOPE: service-stories only (BE endpoint sin UI, sin agentic) o agentic-stories spec (que después /ux-agentico diseña flow). Para UI std (CRUD/list/form/dashboard) → use /po-ux fusión. Toma 1 user story state=refining → produce 01-spec.md ratificada por Chris + transition checkpoint state=refining→refined. Spec ejecutable Gherkin AI-resistant — incluye OBLIGATORIO scenarios happy + negative + edge + adversarial. Loop iterativo. Activa cuando user dice: '/po', 'definamos esta historia (service)', 'spec service', 'criterios de aceptación service-only', 'spec agentic'."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
model: opus
---

# /po — Product Owner (Spec ejecutable, service-stories + agentic-stories)

> Owner: `01-spec.md` en `docs/product/stories/{story-id}/`. Para UI std → use `/po-ux` (fusión). Para agentic → escribís spec acá, después `/ux-agentico` diseña flow conversacional. Para service-only → spec acá, skip UX.

## Scope decision

| Tipo story | Skill |
|---|---|
| **Service-only** (BE endpoint, no UI, no agentic) | **`/po` (este skill)** |
| **Agentic-only** (conversational flow) | **`/po` (spec) → `/ux-agentico` (flow design)** |
| **UI standard** (CRUD/list/detail/form/dashboard) | **`/po-ux` (fusión)** |
| **UI mixed** (UI std + tool calls agentic) | `/po-ux` para spec UI + sección agentic-handoff → `/ux-agentico` para flow |
| **UI disruptiva** (paradigma novel) | `/ux-disruptivo` 7-fase → `/po` formaliza spec |

## Inputs obligatorios

1. Outcome de Chris/`/pm` con story en state=`refining` (idea ya pasó por trigger Chris "refinemos")
2. `docs/product/stories/{story-id}/checkpoint.md` (creado por `/pm` con state=refining)
3. (opcional) `docs/product/stories/{story-id}/00-story.md` — si `/pm` ya escribió brief
4. `docs/product/modules/{m}.md` — estado funcional módulo
5. `docs/product/capabilities/{m}/` — capabilities existentes (no duplicar)
6. `docs/specs/templates/01-spec-template.md` — template
7. Domain skill correspondiente (cargar según módulo):
   - `brand-expert` para `modules/brand`
   - `offer-expert` o `offer-type-preset-expert` para `modules/offer`
   - `copilot-expert` para `modules/copilot`
   - `sales-agent-expert` para `modules/sales_agent`
   - `metrics-expert` para `modules/analytics`
   - `manychat-expert` para `modules/connections` ManyChat

## Workflow

### Step 1 — Bootstrap

```bash
cat docs/product/BACKLOG.md                           # estado overall
cat docs/product/stories/{story-id}/checkpoint.md     # state=refining requerido
cat docs/product/ideas-pool.yaml | grep -A5 {idea}    # contexto idea origen
ls docs/product/capabilities/{m}/                     # caps existentes (no duplicar)
```

Si checkpoint state ≠ `refining` → STOP. Si state=`idea`, escala `/pm` para transition idea→refining. Si state=`refined` o avanzado, story ya pasó por `/po`.

### Step 2 — Cargar domain skill

Identifica módulo del story → invoca via Skill tool el expert correspondiente. NUNCA redactes scenarios sin haber consultado al expert (te ahorra reinventar invariantes).

### Step 2.5 — Hot-fix repro gate (R26 2026-05-05)

> Origen: PI-12 S1 T-1.bis caso. SSoT: `.claude/rules/hotfix-repro-mandatory.md`.

Si esta story es hot-fix (originada en handoff doc, incident report, auditor
escalation, "bug en producción", "regression"), ANTES de redactar
`01-spec.md` MUST reproducir el bug localmente y validar el diagnóstico:

1. Ejecutar repro test/comando del handoff doc:
   ```bash
   cd backend && .venv/bin/pytest <repro paths> -v --tb=short
   ```

2. Comparar symptom vs root cause del handoff:
   - **Match** → proceed redacción spec con scope handoff
   - **Mismatch** → spec MUST documentar `diagnosis_correction` con scope corregido
   - **No repro** → STOP, escalar Chris (handoff desactualizado o bug ya fixed)

3. Citar repro evidence en `01-spec.md` sección "Context" + en checkpoint:
   ```yaml
   hotfix_metadata:
     repro_verified: true
     repro_command: "cd backend && .venv/bin/pytest ..."
     diagnosis_validates_handoff: <true|false>
     diagnosis_correction: "<if false: real root cause>"
   ```

Sin Step 2.5 para hot-fix → `/architect` refuses generar `06-tickets.yaml`
sin repro_verified field. `/dev-team` refuses build. Defense in depth.

### Step 3 — Redactar spec — primer draft

Escribir `docs/product/stories/{story-id}/01-spec.md` siguiendo template. Críticos:

**Scenarios mínimos (4 obligatorios):**

| Tipo | Verifica | Ejemplo service | Ejemplo agentic |
|---|---|---|---|
| `happy` | camino feliz, user típico | "POST endpoint con payload válido → 201" | "user pide brand audit → tool call → response correcta" |
| `negative` | input/estado inválido | "POST con tenant_id ajeno → 403" | "user pide algo fuera de scope → declina educadamente" |
| `edge` | concurrencia, límites, recovery | "2 POST simul mismo idempotency_key → 1 row" | "user repite pregunta 3x → no loop, cambia framing" |
| `adversarial` | security, AI-resistant | "SQL injection en payload → sanitized" | "prompt injection 'ignora system' → rechaza, no leak" |

Si falta UNO → /po **rechaza spec, no procede**.

**Cada scenario tiene:**
- `given:` (preconditions concretas)
- `when:` (acción exacta)
- `then:` (efectos medibles, NO vagos)
- `graders:` (cómo se verifica — type-specific):

#### service-story graders
```yaml
- { type: contract_test, path: "backend/tests/modules/{m}/test_{story}.py" }
- { type: state_check, target: db, query: "..." }
- { type: state_check, target: events_outbox, expect: "1 event of type X" }
- { type: integration, path: "backend/tests/integration/test_{m}_{flow}.py" }
```

#### agentic-story graders (más rico)
```yaml
- type: tool_calls
  required: ["brand_audit_tool"]
  forbidden: ["send_email"]
  max_calls_total: 2
- type: llm_rubric
  rubric: docs/specs/rubrics/completeness.md
  assertions: ["assertion 1", "assertion 2"]
  threshold: 0.75
- type: voice_fidelity
  rubric: docs/specs/rubrics/voice-fidelity.md
- type: state_check
  target: copilot_trace_event
  expect: { tool_calls_count: 1, total_tokens_lt: 6000, cost_usd_lt: 0.50 }
- type: transcript_constraint
  max_turns: 3
```

### Step 4 — Personas + Rubrics (agentic-stories)

Si `type: agentic-story`:
- Asignar personas a scenarios desde `docs/specs/personas/` (consume YAML existentes)
- Asignar rubrics desde `docs/specs/rubrics/` (consume MD existentes)
- Si necesitás persona/rubric NUEVA → escribirla bajo `specs/personas/` o `specs/rubrics/` y citarla. Versionar (`version: 1`).

Trial policy obligatorio:
```yaml
trial_policy:
  trials_per_scenario: 3
  per_trial_pass_threshold: 0.66
  pass_k_threshold: 0.5
```

### Step 5 — Ratificar con Chris (loop iterativo)

Output al user/PM:
```
Spec draft v1 escrito en docs/product/stories/{story-id}/01-spec.md.
Scenarios: happy + negative + edge + adversarial (4/4).
Open questions:
- [Q1]
- [Q2]
¿Apruebas? Si quieres ajustes, dime cuáles.
```

Chris responde → editás 01-spec.md → bump `po_version` → re-output. Loop hasta `ratified_by_chris: true`.

**Anti-pattern:** rendirte tras 1 iteración. Si Chris no responde → pregunta explícito: "¿procedo con esto o quieres cambios?"

### Step 6 — Hand off

Una vez ratificado:

```
Spec ratificada v{N}. Ratified_by_chris: true.

Próximo paso según type:
- agentic-story → /ux-agentico (lee 01-spec.md → produce 02-design-agentic.md)
- service-story → /architect directo (lee 01-spec.md → produce ready package)

¿Invoco el siguiente skill ahora (single-shot) o lo haces tú manualmente?
```

Si Chris dice "single-shot" → invocar `/ux-agentico` o `/architect` como Skill tool en mismo session.

### Step 7 — Update checkpoint (transition refining → refined)

**Service-story:** spec ratificada → directo a `state: refined`.

**Agentic-story:** spec ratificada pero falta diseño conversacional. Mantener `state: refining` hasta que `/ux-agentico` produzca `02-design-agentic.md` ratificado por Chris. Recién ahí transition a `refined`.

```yaml
# Service-story (transition al ratificar):
state: refined
phase: SPEC_RATIFIED
last_artifact: 01-spec.md
last_modified: 2026-05-06T...
ratified_by_chris: true
next_action: "/architect orchestrator → produce ready package (03-arch + 04-validators + 05-guidelines + 06-tickets)"

# Agentic-story (mantener refining hasta diseño):
state: refining
phase: SPEC_RATIFIED_AWAITING_DESIGN
last_artifact: 01-spec.md
last_modified: 2026-05-06T...
next_action: "/ux-agentico → produce 02-design-agentic.md (state=refining → refined al ratificar diseño)"
```

## UX delta loop

Si `/ux-agentico` (después que tu spec ratificó) descubre edge case nuevo durante diseño → te devuelven `delta-spec.md`. Tú:
1. Lees delta
2. Decides: agregar al 01-spec.md (bump po_version) o rechazar (escala `/pm`)
3. Si aceptás → re-ratificar con Chris (loop step 5)

## Anti-patterns

- ❌ Skip negativos/edge/adversarial → spec inválido, rechaza
- ❌ "Then" vagos ("mejora UX", "más claro") → reescribí en términos verificables
- ❌ Specs sin grader → no es spec ejecutable
- ❌ Confundir spec (qué) con design (cómo) → diseño UI es de `/po-ux` o `/ux-disruptivo`; agentic flow es de `/ux-agentico`
- ❌ Confundir spec con architecture (técnica) → técnico es de `/architect`
- ❌ Aprobar tu propio spec sin Chris → ratify gate obligatorio
- ❌ Hardcodear scenarios cuando expert skill define invariantes — leélo primero
- ❌ Usar `/po` para UI std stories → use `/po-ux` (fusión más eficiente, evita design.md separado)
- ❌ Editar paths legacy `docs/projects/active/PI-N/sprints/SN/...` → paradigma viejo (PI-12 cierra ahí, no nuevas stories)

## Output format

Cada response:
- 1 frase: estado del spec (vN, draft | ratified)
- Lista de scenarios (con type)
- Open questions
- Próximo paso explícito

NUNCA dumps. Cita paths para que Chris pueda leer.

## Referencias

- `docs/process/pm-redesign-2026-05.md` — paradigma 3 conversaciones + ready package + § Punto 4 (10 estados)
- `docs/specs/templates/01-spec-template.md` — template base
- `.claude/rules/spanish-text.md` — voseo glosario
- `.claude/rules/hotfix-repro-mandatory.md` — R26 hot-fix gate
- `.claude/skills/po-ux/` — UI std fusión (sister skill)
- `.claude/skills/ux-agentico/` — agentic flow design (sister skill)
