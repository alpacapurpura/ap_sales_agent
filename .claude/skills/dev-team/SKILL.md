---
name: dev-team
description: "Developer team router. Toma 1 ticket de 04-tickets.yaml. Decide owner según owner_eligibility (qwen-opencode preferido para BE/FE no-agentic; Opus 4.7 obligatorio para AGENTIC). Para qwen → invoca via Bash con prompt pre-cocido. Para Opus → spawna agent builder-{be,fe,agentic}. Mantiene T-{n}-impl-log.md vivo. TDD obligatorio. Corre /test-{backend,frontend} + Playwright + agentic evals. Push commit. Update ticket state. Activa cuando user dice: '/dev-team', 'tomá ticket T-N', 'implementá T-N', 'arrancá build'."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Agent
---

# /dev-team — Developer Team Router

> Owner: `T-{n}-impl-log.md` + `T-{n}-result.md`. Toma 1 ticket → ejecuta TDD → push.

## Inputs obligatorios

1. `04-tickets.yaml` — pila tickets del story
2. Ticket específico que tomás (`T-{n}` con `state: ready`)
3. `T-{n}-handoff.md` — input self-contained (architect lo escribió)
4. Story YAML + spec + design + arch (lectura referencia)

## Step 0 — Phase 0: Context pre-flight (MANDATORY antes de Step 1)

> Origen: process-improvement 2026-05-05 R1. Sin context-builder cada subagent
> re-lee 30-50k tokens de spec+arch+rules. Brief Haiku 5-8k tokens amortiza.

Antes de tomar ticket, asegurás `CONTEXT-BRIEF.md` fresco existe en story-folder.

```bash
STORY_DIR=docs/projects/active/PI-N/sprints/SN/stories/{id}
BRIEF=$STORY_DIR/CONTEXT-BRIEF.md
LATEST_COMMIT=$(git log -1 --format=%H -- $STORY_DIR)
```

Decidir si spawn context-builder:
- `CONTEXT-BRIEF.md` no existe → SPAWN
- `CONTEXT-BRIEF.md` existe + header `Faithfulness flag: blocking` → SPAWN (re-build con corrections)
- `CONTEXT-BRIEF.md` existe + más viejo que último commit story → SPAWN (stale)
- `CONTEXT-BRIEF.md` existe + flag `clean|partial` + fresco → SKIP

Si SPAWN:
```
Agent({
  description: "Build context brief for ticket T-{n}",
  subagent_type: "context-builder",
  model: "haiku",
  prompt: "<pr_folder>: <absolute path STORY_DIR>;
           <modules>: <comma list from story.yaml `modules` field>;
           <phase>: builder;
           <subsystem_keywords>: <if you know, comma list — else context-builder auto-infiere H2>;
           <frameworks>: <if known frameworks involved — fastapi, langgraph, anthropic, sqlalchemy, pydantic, etc.>"
})
```

Espera context-builder + context-validator (cadena interna). Lee `CONTEXT-BRIEF.md` header:
- `Faithfulness flag: clean` → proceder Step 1
- `Faithfulness flag: partial` → leer §11 gaps, decidir si downstream puede tolerar (típicamente sí — gaps documentados)
- `Faithfulness flag: blocking` → STOP. Reportar Chris: contexto incompleto, validator escaló blocking. Re-spawn con corrections o escalate.

**Pasás `CONTEXT-BRIEF.md` path en TODO prompt subagent downstream** (Step 2A/B/C). Builder/auditor agents YA tienen mandatory initial read clausula que prefiere brief sobre raw docs.

## Step 0.5 — Hot-fix repro gate (R26 2026-05-05)

> Origen: PI-12 S1 T-1.bis 2026-05-05 (`docs/process/learnings.md`).
> SSoT: `.claude/rules/hotfix-repro-mandatory.md`.

ANTES de spawn builder para hot-fix ticket, reproduce el bug localmente.

Aplica si ticket tiene AL MENOS UNA señal:
- Title/context contiene `bug`, `hot-fix`, `regression`, `incident`, `bis`, `revert`, `fix forward`
- Origin field menciona `handoff doc`, `pase a producción failed`, `auditor escalation`
- Sub-numero `T-N.bis`
- Spec describe symptom (no design from scratch) + scope quirúrgico ≤2h

Workflow:

1. **Reproduce localmente:**
   ```bash
   # Run repro command from handoff doc / ticket context section
   cd backend && .venv/bin/pytest <repro_test_paths> -v --tb=short
   ```
   Captura output verbatim.

2. **Diagnóstico real:**
   - ✅ **Match:** symptom + traceback + log lines coinciden con causa
     propuesta → handoff VALIDADO. Proceed con scope handoff.
   - ⚠️ **Mismatch:** symptom existe pero apunta a código distinto del
     scope propuesto → handoff MISDIAGNOSED. STOP, re-redactar ticket
     spec con scope correcto, document `diagnosis_correction` field en
     ticket.repro_evidence.
   - ❌ **No repro:** test pasa o handoff desactualizado → STOP.
     Close ticket `superseded` o escalate Chris.

3. **Cite repro evidence en ticket entry de `04-tickets.yaml`:**
   ```yaml
   repro_verified: true
   repro_evidence:
     command: "cd backend && .venv/bin/pytest <paths> -v"
     output: |
       <verbatim error/traceback first 5-10 lines>
     diagnosis_validates_handoff: <true|false>
     diagnosis_correction: "<if false: real root cause + scope correction>"
   ```

4. **Spawn builder**: prompt MUST cite `repro_verified: true`. Si
   `repro_verified: false` o ausente → REFUSE spawn:
   ```
   ERROR — hot-fix ticket missing repro_verified per
   .claude/rules/hotfix-repro-mandatory.md. Run repro command first,
   document evidence, then proceed.
   ```

Step 0.5 protege contra el ~$8 USD waste/builder-run que ocurriría con
scope mal-spec'd. T-1.bis caso origen ahorra ~30min wall-clock + 1 builder
re-spawn cuando handoff está mis-diagnosed.

## Step 1 — Tomar ticket

```bash
cat docs/projects/active/PI-N/sprints/SN/stories/{id}/04-tickets.yaml
```

Filtrar tickets con `state: ready` (deps cumplidas).

Decidir owner según `owner_eligibility` + `production_code` flag (R23 2026-05-05):

| Surface | production_code | Owner preferido | Razón |
|---|---|---|---|
| BE no-agentic | true | qwen-opencode | costo, qwen capable |
| BE no-agentic | false (tests/docs/tooling) | qwen-opencode o claude-sonnet | trivial test/doc work |
| FE no-agentic | true | qwen-opencode | costo, qwen capable |
| FE no-agentic | false | qwen-opencode | trivial |
| AGENTIC | true | claude-opus (MISMA sesión, NO opencode) | brand voice + protected surfaces + Opus prompt eng |
| **AGENTIC** | **false (tests/docs only)** | **claude-sonnet** | **R23 — test-only/doc-only sobre módulo agentic NO requiere Opus** |
| Migration aislada | true | qwen-opencode | trivial DDL |
| Cross-module shared | true | claude-sonnet o opus | complexity |

**Reglas hard:**
- AGENTIC ticket + `production_code: true` → SIEMPRE Opus 4.7. Esto se ejecuta en MISMA sesión Claude Code (tú como /dev-team con Opus).
- AGENTIC ticket + `production_code: false` → Sonnet OK. Tests/docs/tooling
  sobre `modules/{copilot,sales_agent}/` no requieren Opus reasoning. Valida-
  ción gate downstream (R3) cubre regression risk.
- Si no estás en Opus y ticket=AGENTIC + production_code=true → STOP, escala
  Chris: "necesito Opus 4.7 para este ticket. Cambiame de modelo."

**Owner override logic (R23 dynamic):**
```
if ticket.production_code == false:
    if ticket.surface in ["BE", "FE"]:
        owner = qwen-opencode  # trivial — cheapest capable
    elif ticket.surface == "AGENTIC":
        owner = claude-sonnet  # tests/docs sobre agentic — Sonnet capable
elif ticket.surface == "AGENTIC" and ticket.production_code == true:
    owner = claude-opus  # HARD rule, brand voice protected
elif ticket.surface in ["BE", "FE"]:
    owner = qwen-opencode  # default for production code
```

**Origen R23 (2026-05-05 caso T-1.bis):** test-only ticket en Story A
agentic-adjacent forzó Opus 4.7 ($8 USD wasted) cuando Sonnet capable.
production_code flag corrige policy estática.

Update `04-tickets.yaml` ticket `T-{n}`:
```yaml
state: assigned
assigned_to: qwen-opencode | claude-opus | claude-sonnet
assigned_at: 2026-05-04T...
transitions:
  - { state: assigned, at: ..., by: "/dev-team", to: "<owner>" }
```

Crear `T-{n}-impl-log.md` con plan inicial.

## Step 2A — Owner = qwen-opencode (BE/FE no-agentic)

```bash
# Construir prompt para qwen
cat > /tmp/T-{n}-qwen-prompt.md <<EOF
Eres developer Nicolify ejecutando T-{n} de story {id}.

PRIORITY READ — CONTEXT-BRIEF (Haiku-built, 5-8k tokens, contiene spec+arch+rules+anti-dup+canonical docs):
- $(realpath docs/projects/active/PI-N/sprints/SN/stories/{id}/CONTEXT-BRIEF.md)

Lee TAMBIÉN estos archivos (referencia profunda si brief insuficiente):
- $(realpath docs/projects/active/PI-N/sprints/SN/stories/{id}/05-impl/T-{n}-handoff.md)
- $(realpath docs/projects/active/PI-N/sprints/SN/stories/{id}/01-spec.md) — sección scenarios relevantes
- $(realpath docs/projects/active/PI-N/sprints/SN/stories/{id}/03-arch-{be|fe}.md)

Reglas TDD obligatorias:
1. RED: escribí tests que fallen primero
2. GREEN: implementá mínimo para pasar
3. REFACTOR: limpiar

Convenciones (.claude/rules/*):
- backend-ddd.md o frontend-fsd.md
- tenant-isolation.md
- spanish-text.md (Spanish neutro, no voseo)
- backend-migrations.md (idempotente)

Quality gates antes push:
- /test-backend o /test-frontend completo verde
- Coverage no baja
- Mypy strict si aplica

Mantenelo el T-{n}-impl-log.md actualizado VIVO mientras trabajás.

Output al terminar:
- T-{n}-result.md con diff resumen + quality gates output literal + commit SHA
- Estado ticket: pushed
EOF

# Invocar opencode con qwen
cd /home/chris/AISALESHT
opencode run \
  --prompt-file /tmp/T-{n}-qwen-prompt.md \
  --workspace /home/chris/AISALESHT \
  --model qwen-coder \
  --max-iterations 50

# Si opencode falla / API no disponible → fallback: copiá prompt + Chris ejecuta manual:
# echo "Pegá esto en opencode CLI: $(cat /tmp/T-{n}-qwen-prompt.md)"
```

Mientras qwen trabaja → vos NO interferís. Cuando termina:
1. Verificás `T-{n}-result.md` existe y dice `state: pushed`
2. Verificás commit SHA en git log
3. Actualizás `04-tickets.yaml` ticket → state: pushed
4. Hand off `/auditor`

## Step 2B — Owner = claude-opus (AGENTIC)

Spawnás agent `builder-agentic` (Opus 4.7) via Agent tool:

```
Agent({
  description: "Build agentic ticket T-{n}",
  subagent_type: "builder-agentic",
  prompt: "<pr_folder>: docs/projects/active/PI-N/sprints/SN/stories/{id}/
           CONTEXT-BRIEF.md (priority read — 5-8k tokens compresses spec+arch+rules+anti-dup+canonical docs)
           <files_to_read>: docs/projects/.../T-{n}-handoff.md, 01-spec.md, 03-arch-agentic.md, 02-design-agentic.md, story YAML
           Skill consultados obligatorio: copilot-expert/sales-agent-expert + tessl__langgraph + claude-api + graceful-degradation
           TDD: eval goldens RED first, integration tests, tools tests, etc
           Output: T-{n}-result.md + commit pushed
           Last line: done -> path/to/T-{n}-result.md"
})
```

`builder-agentic` corre tests + eval suite (`pytest tests/agentic_evals/{m}/{story}_eval.py --trials=3`) + push. Devuelve `done -> T-{n}-result.md`.

## Step 2C — Owner = claude-sonnet (cross-module shared)

Spawnás agent `builder-backend` o `builder-frontend` con model=sonnet (default). Prompt SIEMPRE referencia `CONTEXT-BRIEF.md`:

```
Agent({
  description: "Build {surface} ticket T-{n}",
  subagent_type: "builder-{backend|frontend}",
  model: "sonnet",
  prompt: "<pr_folder>: docs/projects/active/PI-N/sprints/SN/stories/{id}/
           Read CONTEXT-BRIEF.md FIRST (saves 30-50k tokens vs raw docs).
           <files_to_read>: T-{n}-handoff.md, 01-spec.md, 03-arch-{be|fe}.md, story.yaml
           TDD obligatorio. ...
           Last line: done -> path/to/T-{n}-result.md"
})
```

## Step 3 — Self-monitor durante build

Mientras el dev (qwen | builder-{be,fe,agentic}) trabaja, vos:
- Touchéas `T-{n}-impl-log.md` periodically con timestamps "still in progress"
- Si dev se cuelga > 30min sin progress visible → escala Chris
- Si dev reporta `blocked` → registrar en log + escala /pm

## Step 4 — Verificar result + gate-runner enforcement

Cuando dev termina, leer `T-{n}-result.md` + verificar `gate-output.json`:

- [ ] Acceptance criteria self-verified table → todas ✅?
- [ ] **`gate-output.json` existe en story-folder + `overall.any_fail = false`?**
      Si missing → builder no invocó gate-runner. SPAWN gate-runner directo aquí:
      ```
      Agent({
        description: "Force gate-runner T-{n}",
        subagent_type: "gate-runner",
        model: "haiku",
        prompt: "<pr_folder>: docs/projects/active/PI-N/sprints/SN/stories/{id}/;
                 <command>: test-{backend|frontend|all};
                 <iter>: <N>"
      })
      ```

      **R22 post-spawn validation (origen 2026-05-05 caso T-1.bis):**
      Después del spawn, VERIFY el artifact realmente escribió a disco. Si gate-runner
      reporta "ERROR — gate-output.json write failed" en su last-line, OR si el
      file no existe post-spawn, NO confíes en stdout output del agent — re-spawn
      UNA segunda vez con mismo prompt. Si segunda invocación también falla:
      ```bash
      # Fallback manual: orchestrator escribe gate-output.json directo
      cd /home/chris/AISALESHT/backend && .venv/bin/{ruff,pytest} ... > /tmp/gate.log 2>&1
      # Compose JSON manually with schema:
      python3 -c "import json; ..." > <pr_folder>/gate-output.json
      ```
      Documentar en T-{n}-impl-log.md sección "Gate-runner failover" + escalar
      backlog R22 retry.

      Read JSON. Si `any_fail=true` → ticket vuelve a `tests-failing`, hand off /dev-team con findings.
- [ ] Commit SHA presente + git log lo confirma?
- [ ] Push exitoso (`git push origin development`)?

Si cualquier gap → ticket vuelve a `tests-failing` o `building`. Si dev itera ≥5x sin éxito → `blocked` + escala.

> **Origen R2 process-improvement 2026-05-05 (D2):** sin gate-runner enforcement
> orchestrator, cada subagent corre su propio pytest cycle (~10-15% tokens
> duplicados). gate-runner Haiku produce JSON estructurado consumible por auditor
> sin re-correr suite ni parsear stdout.

## Step 5 — Hand off /auditor

Update `04-tickets.yaml`:
```yaml
state: pushed
push_commit_sha: abc1234
transitions:
  - { state: tests-passing, ... }
  - { state: pushed, ..., commit: "abc1234" }
```

Output:
```
T-{n} pushed (commit abc1234).
Acceptance criteria self-verified: A1✅ A2✅ A3✅
Quality gates: /test-backend verde
Próximo: /auditor lee T-{n}-result.md + corre tests independientes.
```

Update checkpoint:
```
phase: DEV_T{n} → AUDIT_T{n}
last_artifact: T-{n}-result.md
next_action: "/auditor toma T-{n} para review"
```

## Step 5.5 — R12 layer 1: emit process metric

> Origen: process-improvement A1 partial (2026-05-05). Foundation para
> medir ROI cross-PI. Token-level detail viene del transcript via
> `scripts/extract_baseline_metrics_from_transcripts.py`; aquí emitimos
> orchestrator-level metadata (verdict + commit_sha + ticket + phase) que
> NO está en transcript.

Antes de cerrar Step 5, append metric row a `docs/process/metrics/runs.jsonl`:

```bash
python3 scripts/emit_process_metric.py \
  --pi "PI-N" \
  --sprint "SN-{slug}" \
  --story "{story-id}" \
  --ticket "T-{n}" \
  --phase build \
  --agent-type "<builder-backend|builder-agentic|builder-frontend|qwen-opencode>" \
  --verdict "<tests-passing|tests-failing|pushed|blocked>" \
  --commit-sha "$(git log -1 --format=%h)" \
  --total-tokens "<from agent tool result if visible, else omit>" \
  --tool-use-count "<from agent tool result if visible, else omit>" \
  --duration-ms "<wall-clock ms agent ran, else omit>" \
  --iter <N> \
  --note "<1-line context if relevant>"
```

`runs.jsonl` is gitignored (rolling). Periodic aggregation: post-PI close,
PM runs analysis script comparing `runs.jsonl` to `baseline-pre-R1-R9.jsonl`
to validate R1-R9 ROI.

If `python3 scripts/emit_process_metric.py` fails (script missing, etc.) →
log warning + continue. Metrics emission is best-effort, NEVER blocks the
pipeline. (Pattern coherente con copilot observability — try/except
structlog warning, no rompe turn.)

## Multi-ticket parallel

Si 2 tickets independientes (no `depends_on`) están `ready` simultáneamente:
- Podés spawnear builders en PARALELO (single message, multiple Agent calls / multiple opencode bash)
- IMPORTANTE: ambos no deben tocar mismos archivos (conflict)
- Si overlap detectado → secuencial

## Anti-patterns

- ❌ AGENTIC ticket asignado a qwen (HARD BAN)
- ❌ Skip TDD (escribir código sin test RED primero)
- ❌ `git add .` / `git add -A` / `git add -u` (parallel-safety)
- ❌ `git commit --no-verify`
- ❌ `git pull` antes commit (parallel-safety)
- ❌ Push falla non-fast-forward → NO `git pull`. STOP, escala.
- ❌ Marcar ticket pushed sin verify quality gates verde
- ❌ Self-fix más de 5 iteraciones sin escalar bloqueo
- ❌ Dev tocando archivos out_of_scope del ticket
- ❌ Dumpear código en chat (anti-teléfono — todo en archivos)

## Output format

Cada update al user/PM:
- 1 frase status ticket
- Quality gates resumen
- Próximo paso
- NO dump de diff o tests output (cita paths)
