# Prompt — Context prep (Haiku pre-flight)

> **MANDATORY for PR ≥ M (medium).** Skip for PR S (bug-fix simple, refactor de un archivo) — overhead spawn > ahorro.
>
> Spawn `nicolify-context-builder` (Haiku 4.5) BEFORE architect / builder / auditor. Produces `CONTEXT-BRIEF.md` 3-5k tokens that downstream Opus/Sonnet agents consume INSTEAD of re-reading 30-50k of docs.
>
> **Critical reinforcement (origin: PR-3 PI-2 audit failure 2026-04-30):** § 7 + § 8 of CONTEXT-BRIEF do the cross-module duplicate scan that prevents architect from inventing parallel layers. The Haiku does this work; the Opus architect inherits the result.

## Spawn pattern (Agent tool)

```
Agent({
  description: "Pre-flight PR-{n}",
  subagent_type: "nicolify-context-builder",
  model: "haiku",
  prompt: <bloque abajo con valores reales>
})
```

## Prompt body

```
Genera CONTEXT-BRIEF.md para este PR.

<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}
<modules>: {list — e.g., "copilot, brand" or "sales_agent" or "offer, analytics"}
<phase>: {architect | builder | auditor}
<subsystem_keywords>: {RECOMMENDED for architect phase — comma-list of subsystem keywords driving duplicate scan}

Examples of <subsystem_keywords>:
- LLM/agentic PR: "llm, model_routing, provider"
- Cache PR: "cache, prompt_cache"
- Queue/outbox: "queue, outbox, event"
- Auth: "auth, session, clerk"
- Observability: "observability, trace, metrics"
- Billing/cost: "billing, cost, pricing"
- Rate limit: "rate_limit, throttle"
- Scheduler: "scheduler, cron, follow_up"
- Webhook: "webhook, callback"

Sigue tu workflow estándar:
1. Read <pr_folder> files (PR.md, CONTRACT.md if exists, UI-SPEC.md if exists, IMPL-LOG.md if exists, REVIEW*.md if exists)
2. Read current-state/{module}.md per <modules>
3. Load relevant rules per <phase> + <modules>
4. Run git diff main..HEAD --stat + --name-only
5. **Duplicate detection scan** (MANDATORY for architect/builder phase) — execute the 6 grep commands per <subsystem_keywords> against backend/src/core/, backend/src/shared/, frontend/ if applicable
6. Write CONTEXT-BRIEF.md with §1-§13 schema fully populated
   - § 7 Existing systems detected — verbatim grep results, table format
   - § 8 EXTEND-vs-NEW recommendations — mechanical rule (≥80% overlap → EXTEND, 40-79% → EXTEND with caveat, none → NEW)
   - § 11 Faithfulness gaps — flag any scan-incomplete or truncated reads
   - § 13 Verbatim grep commands executed (reproducibility)

Output path: <pr_folder>/CONTEXT-BRIEF.md

Last line of reply MUST be:
<!-- @pm: CONTEXT-BRIEF.md ready (faithfulness: clean|partial). Downstream agent ({architect|builder|auditor}) can consume it now. -->
```

## Cómo usar

1. Reemplazar `{X}`, `{theme}`, `{N}`, `{n}`, `{slug}` con valores reales del PR.
2. Decidir `<modules>` desde PR.md (qué módulos toca el PR).
3. Decidir `<phase>` según fase actual de orquestación (architect first, builder después, auditor final).
4. Para `<phase>: architect`: pasar `<subsystem_keywords>` SIEMPRE (lo que el PR introducirá: nuevo provider LLM → "llm"; nuevo job background → "queue"; etc.).
5. PM o builder spawnea con Agent tool — ver pattern arriba.

## Cuándo NO ejecutar

- PR S (small bug-fix de un solo archivo, typo, refactor < 30 LOC) — overhead spawn > ahorro.
- Re-audit con CONTEXT-BRIEF.md ya generado y vigente (mismo commit hash) — context-builder es idempotente, output sería igual.

## Anti-patterns

- ❌ Spawn context-builder sin `<subsystem_keywords>` en phase=architect (pierde valor de § 7 + § 8 — duplicate scan se hace genérico)
- ❌ Architect ignora § 7 + § 8 del brief al diseñar (duplicado downstream → audit FAIL "NO-NEW-LAYER violation")
- ❌ PR M+ skipping context-builder (desperdicia 30-50k input tokens al Opus downstream)
- ❌ Spawn context-builder con `model: "sonnet"` (es Haiku — overcost 5×)
- ❌ Re-leer todo el repo después del brief porque "no confío en Haiku" (la pre-validación es § 11 Faithfulness — si flag clean, confía)

## Auto-loop integration

En el flujo PM completo:

```
00-context-prep    (Haiku)   ← este prompt
   ↓
01-architect-start (Opus)    ← lee CONTEXT-BRIEF.md, produce CONTRACT.md
   ↓
02-builder-start   (Sonnet o Opus para agentic)  ← lee CONTEXT-BRIEF + CONTRACT + spawnea gate-runner Haiku + auditor Opus
   ↓
03-auditor-start   (Opus)    ← lee CONTEXT-BRIEF + gate-output.json + diff
   ↓
04-pm-close        (PM)      ← lee REVIEW.md + actualiza current-state
```

Para fix-loop iteraciones (iter 2-3): NO re-spawn context-builder. El brief original se mantiene válido (mismo PR, mismo módulos). Builder/auditor re-leen el mismo brief — cache prefix se mantiene byte-idéntico → 80%+ del input cached.
