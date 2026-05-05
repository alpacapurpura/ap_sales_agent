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

## Step 1 — Tomar ticket

```bash
cat docs/projects/active/PI-N/sprints/SN/stories/{id}/04-tickets.yaml
```

Filtrar tickets con `state: ready` (deps cumplidas).

Decidir owner según `owner_eligibility`:

| Surface | Owner preferido | Razón |
|---|---|---|
| BE no-agentic | qwen-opencode | costo, qwen capable |
| FE no-agentic | qwen-opencode | costo, qwen capable |
| AGENTIC | claude-opus (este session, NO opencode) | brand voice + protected surfaces + Opus prompt eng |
| Migration aislada | qwen-opencode | trivial |
| Cross-module shared | claude-sonnet o opus | complexity |

**Reglas hard:**
- AGENTIC ticket → SIEMPRE Opus 4.7. Esto se ejecuta en MISMA sesión Claude Code (vos como /dev-team con Opus).
- Si no estás en Opus y ticket=AGENTIC → STOP, escala Chris: "necesito Opus 4.7 para este ticket. Cambiame de modelo."

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

## Step 4 — Verificar result

Cuando dev termina, leer `T-{n}-result.md`:

- [ ] Acceptance criteria self-verified table → todas ✅?
- [ ] Quality gates output paste → verde?
- [ ] Commit SHA presente + git log lo confirma?
- [ ] Push exitoso (`git push origin development`)?

Si cualquier gap → ticket vuelve a `tests-failing` o `building`. Si dev itera ≥5x sin éxito → `blocked` + escala.

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
