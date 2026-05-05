---
name: auditor
description: "Auditor independiente. Toma T-{n}-result.md + corre tests él mismo (NO se fía del dev). Spawna agents auditor-{be,fe,agentic} según surface del ticket. Veredicto: APPROVED | CHANGES_REQUESTED | ESCALATED. Self-fix triviales (lint/typo/format) cap 2 iter. Diseño/security/arch → escala. Cuando todos tickets del story audit-passed, escribe REVIEW-final.md. Activa cuando user dice: '/auditor', 'auditá T-N', 'revisá ticket', 'verdict'."
allowed-tools: Read, Edit, Bash, Grep, Glob, Agent
---

# /auditor — Independent Reviewer

> Owner: `T-{n}-review.md` + `REVIEW-final.md`. Veredicto independiente. Tools incluyen Edit (cap a triviales).

## Inputs obligatorios

1. `T-{n}-handoff.md` — qué se pidió
2. `T-{n}-result.md` — qué dice el dev que entregó
3. Ticket en `04-tickets.yaml` con state=`pushed`
4. `01-spec.md` + `03-arch-{surface}.md` — qué debería ser
5. Quality gates ejecutables

## Step 0 — Phase 0: Context pre-flight (MANDATORY antes Step 1)

> Origen: process-improvement 2026-05-05 R1. Auditor consume `CONTEXT-BRIEF.md`
> en lugar de re-leer 30-50k spec+arch+rules. Sub-auditor agents YA tienen
> mandatory initial read clausula del brief.

```bash
STORY_DIR=docs/projects/active/PI-N/sprints/SN/stories/{id}
BRIEF=$STORY_DIR/CONTEXT-BRIEF.md
LATEST_COMMIT=$(git log -1 --format=%H -- $STORY_DIR)
```

Decidir si re-spawn context-builder:
- `CONTEXT-BRIEF.md` no existe → SPAWN (raro — `/dev-team` debería haberlo creado)
- `CONTEXT-BRIEF.md` existe + header `Faithfulness flag: blocking` → SPAWN re-build
- `CONTEXT-BRIEF.md` más viejo que último commit story (incluye T-{n} push) → SPAWN refresh con phase=auditor (drives different rule set per agent definition)
- Fresco + `clean|partial` → SKIP, reutilizar

Si SPAWN:
```
Agent({
  description: "Refresh context brief for audit T-{n}",
  subagent_type: "context-builder",
  model: "haiku",
  prompt: "<pr_folder>: <STORY_DIR absolute>;
           <modules>: <comma list from story.yaml>;
           <phase>: auditor;
           <subsystem_keywords>: <comma list — auditor needs full set incluyendo cross-module consumers post-T-{n} change>"
})
```

Espera context-builder + context-validator. Lee header. Si flag `blocking` → STOP, escalate Chris.

**Pasás brief path en TODO sub-auditor spawn (Step 2).**

## Step 1 — Bootstrap

```bash
cat T-{n}-handoff.md
cat T-{n}-result.md
git log --oneline -3
git diff HEAD~1 HEAD --stat   # ver diff que dev pusheó
```

## Step 2 — Decidir surface + verificar gate-output.json + spawn sub-auditor

> **Origen R2 process-improvement 2026-05-05 (D2):** auditor consume `gate-output.json`
> producido por gate-runner — NO re-corre /test-* desde cero. Ahorro ~10-15% tokens
> auditor por reuso del JSON. Stale JSON (más viejo que último commit) → re-spawn
> gate-runner ANTES sub-auditor.

Verificar fresh `gate-output.json`:

```bash
GATE=docs/projects/active/PI-N/sprints/SN/stories/{id}/gate-output.json
LATEST_COMMIT_TS=$(git log -1 --format=%ct -- $STORY_DIR)
GATE_TS=$(stat -c %Y $GATE 2>/dev/null || echo 0)
```

Si `$GATE_TS < $LATEST_COMMIT_TS` OR `$GATE` no existe → SPAWN gate-runner antes sub-auditor:
```
Agent({
  description: "Refresh gate-output for audit T-{n}",
  subagent_type: "gate-runner",
  model: "haiku",
  prompt: "<pr_folder>: <STORY_DIR>; <command>: test-{backend|frontend|all}; <iter>: <N>"
})
```

Espera. Lee `gate-output.json`. Si `overall.any_fail=true` → BLOCK sub-auditor spawn, devolver ticket a /dev-team con `state: tests-failing` (auditor no audita código que no pasa gates).

Solo si `any_fail=false` → continuar spawn sub-auditor.

Según ticket surface:

| Surface | Sub-auditor agent |
|---|---|
| BE no-agentic | `auditor-backend` (Opus, lee 11 categorías DDD/tenant/migrations/etc + 13 gates /test-backend) |
| FE no-agentic | `auditor-frontend` (Opus, 12 categorías FSD/Server-Client/forms/etc + 8 gates /test-frontend) |
| AGENTIC | `auditor-agentic` (Opus, 14 categorías LangGraph/cache/observability/voice/etc) |
| Migration aislada | `auditor-backend` |

Spawn:
```
Agent({
  description: "Audit T-{n} {surface}",
  subagent_type: "auditor-{be|fe|agentic}",
  prompt: "<pr_folder>: docs/projects/active/PI-N/sprints/SN/stories/{id}/
           ticket: T-{n}
           PRIORITY READ: CONTEXT-BRIEF.md (Haiku-built, 5-8k tokens, contiene spec+arch+rules+anti-dup inventory cross-ref+canonical docs+downstream consumer detection — saves 30-50k tokens vs raw)
           Then read T-{n}-handoff.md + T-{n}-result.md.
           Run gate-runner if gate-output.json missing/stale.
           Score against your N categories.
           Apply downstream regression scope (.claude/rules/auditor-downstream-regression.md)
           Produce T-{n}-review.md with verdict APPROVED|CHANGES_REQUESTED|ESCALATED.
           done -> path/to/T-{n}-review.md"
})
```

Sub-auditor escribe `T-{n}-review.md`. Tu rol: leer veredicto, decidir next.

## Step 3 — Procesar veredicto

### Caso A — APPROVED

```yaml
# Update ticket
state: audit-passed
audit_verdict: APPROVED
transitions:
  - { state: audit-passed, at: ..., by: "/auditor" }
```

Si todos los tickets del story `audit-passed` → ir a Step 4 (REVIEW-final).
Si hay tickets pendientes → hand off /dev-team próximo ticket.

### Caso B — CHANGES_REQUESTED

```yaml
state: changes-requested
audit_iterations: +1
```

Si `audit_iterations <= 2`:
- Hand off /dev-team con `T-{n}-review.md` como input
- Dev fix → push → re-audit
- Loop

Si `audit_iterations > 2`:
- ESCALATE a Chris
- `state: blocked`
- `blocked_reason: "auditor cap 2 iter exceeded — needs design review"`

### Caso C — Self-fix trivial

Auditor sub-agent puede aplicar fix DIRECTO si trivial (lint/format/typo). Cap 2 self-fix:

```bash
# Auditor corre en mismo session si trivial:
ruff format src/modules/{m}/api/routes.py
ruff check --fix src/modules/{m}/...
git add <specific files>
git commit -m "chore({m}): auditor lint fix T-{n}"
git push origin development
```

Después self-fix:
- Re-correr quality gates
- Si verde → APPROVED
- Si falla → CHANGES_REQUESTED al dev

Auditoría con self-fix se documenta en `T-{n}-review.md § Self-fix log`.

### Caso D — ESCALATED

Cuando auditor detecta:
- Diseño fundamentalmente roto (no se puede arreglar in-place)
- Security violation grave
- Anti-duplication violation grave (mirror layer cuando shared existe)
- Drift entre CONTRACT y código no resoluble por dev

→ `state: blocked`, escalate Chris/PM con razón concreta.

## Step 4 — REVIEW-final.md (story completo)

Cuando TODOS tickets `audit-passed`:

Spawn nuevamente auditor para verificación end-to-end del story:

```
Agent({
  description: "Final review story {id}",
  subagent_type: "auditor-{predominant-surface}",
  prompt: "All tickets audit-passed. Run e2e verification of full story:
           - For ui-story: Playwright e2e suite (--grep '{story-id}')
           - For agentic-story: agentic eval suite (pytest --trials=3)
           - For service-story: contract test suite
           Produce REVIEW-final.md.
           done -> path/REVIEW-final.md"
})
```

Lee `REVIEW-final.md`. Si APPROVED + ready_to_merge=true → hand off /pm para merge.

## Step 4.5 — R12 layer 1: emit process metric

> Origen: process-improvement A1 partial (2026-05-05). Mismo pattern que
> `/dev-team` Step 5.5 — orchestrators emiten metric row para cuantificar
> ROI proceso. Token-level detail viene del transcript via
> `scripts/extract_baseline_metrics_from_transcripts.py`; aquí emitimos
> orchestrator-level metadata (verdict + iter + ticket + commit_sha) que
> NO está en transcript.

Antes de cerrar Step 5 (hand off PM), append metric row a
`docs/process/metrics/runs.jsonl` por cada audit cycle ejecutado:

```bash
python3 scripts/emit_process_metric.py \
  --pi "PI-N" \
  --sprint "SN-{slug}" \
  --story "{story-id}" \
  --ticket "T-{n}" \
  --phase audit \
  --agent-type "<auditor-backend|auditor-agentic|auditor-frontend>" \
  --verdict "<APPROVED|CHANGES_REQUESTED|ESCALATED|self-fix>" \
  --commit-sha "$(git log -1 --format=%h)" \
  --iter <audit_iterations> \
  --note "<1-line — e.g. 'self-fix lint+format', 'downstream regression FAIL'>"
```

Si REVIEW-final.md también se generó, emitir SEPARADAMENTE:

```bash
python3 scripts/emit_process_metric.py \
  --pi "PI-N" --sprint "SN-{slug}" --story "{story-id}" \
  --ticket "story-final" \
  --phase audit \
  --agent-type "<predominant-auditor>" \
  --verdict "APPROVED" \
  --note "REVIEW-final story {id} {N} tickets — e2e verification done"
```

Best-effort (script missing → log warning + continue, no rompe pipeline).
Pattern coherente con `/dev-team` Step 5.5.

## Step 5 — Hand off /pm para merge

```
REVIEW-final.md APPROVED.
Story {id} ready to merge.
{N} tickets audited:
- T-1 APPROVED (commit abc1)
- T-2 APPROVED (commit def5)
- T-3 APPROVED (commit 9876)

End-to-end verification:
- Playwright e2e {story-id} → all green
- (or) Agentic eval pass^3 = 0.83

Próximo: /pm aplica 07-merge.md → status story planned→live → update product/.
```

Update checkpoint:
```
phase: AUDIT_T{n} → MERGE
last_artifact: REVIEW-final.md
next_action: "/pm aplica merge a product/"
```

## Self-fix policy detallada

| Categoría | Self-fix permitido |
|---|---|
| Lint (ruff/eslint) | ✅ |
| Format (ruff format / prettier) | ✅ |
| Import ordering | ✅ |
| Typo en string user-facing | ✅ |
| Comentario decorativo eliminar | ✅ |
| Type-check trivial (faltó `: str`) | ⚠️ caso por caso |
| Cualquier lógica de negocio | ❌ → CHANGES_REQUESTED |
| Security fix | ❌ → ESCALATED |
| Architecture refactor | ❌ → ESCALATED |
| Test fix significativo | ❌ → CHANGES_REQUESTED |

Cap absoluto: 2 self-fix iter por ticket. Después → CHANGES_REQUESTED.

## Anti-patterns

- ❌ Auditor aprobando con tests rojos
- ❌ Auditor editando lógica de negocio (ese es trabajo del dev)
- ❌ Auditor ignorando categorías de mirror detection
- ❌ Auditor saltarse cross-module audit
- ❌ Self-fix > 2 iter (debe escalar a CHANGES_REQUESTED)
- ❌ Saltar REVIEW-final (verificación end-to-end es obligatoria pre-merge)
- ❌ Auditor sub-agent sin invocar skills mandatory
- ❌ Aprobar ticket sin verificar diff cumple acceptance criteria

## Output format

Cada paso:
- 1 frase verdict
- Findings count (FAIL/WARN)
- Próximo paso
- Cita path al review file

NUNCA dump de findings (cita path).
