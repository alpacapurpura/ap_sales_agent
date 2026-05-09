<!-- voseo-allowed: internal skill documentation, not user-facing -->
---
name: handoff
description: "Genera handoff doc al cierre de session — captura git log + uncommitted + last-checkpoint + bootstrap prompt para próxima session. Delegado a Haiku worker (token-cheap). Origen 2026-05-09 G4 — pattern recurring detectado en report. Activa: '/handoff', 'handoff', 'cierra con handoff', 'genera bootstrap', 'pase de mano'."
allowed-tools: Read, Bash, Write, Agent
model: opus
---

# /handoff — Session handoff doc generator

> **Origen:** report.html 2026-05-09 — "Generate handoff prompts proactively" pattern recurring across multiple sessions (Story D deeper bugs, PI-12 S1 wave continuation, PR-2 builder retry, post-migration bootstrap). 162 sessions × ~5-10k tokens manual handoff = significant leak. Haiku-driven cierra esto.

## Cuándo usar

- User dice "cierra con handoff" / "genera bootstrap" / "pase de mano"
- Antes de close limpio cuando hay state complejo en juego (mid-story / mid-build / mid-audit)
- /pm orchestrator detecta context approaching limit → proactive handoff

## Cuándo NO usar

- Session trivial sin state acumulado (< 5 tool calls + nothing committed)
- User dijo "cierra limpio" sin pedir handoff (use `/cierra-limpio` skill — sólo commit pendientes, sin handoff doc)

## Output target

`docs/product/handoffs/YYYY-MM-DD-HHmm.md` — auto-named con timestamp UTC.

## Steps

### Step 1 — Pre-spawn audit (Opus orchestrator)

Capturás contexto antes de spawn Haiku:

```bash
mkdir -p docs/product/handoffs/
TIMESTAMP=$(date -u +%Y-%m-%d-%H%M)
HANDOFF_PATH="docs/product/handoffs/${TIMESTAMP}.md"

# Estado git
git status --short
git log --oneline -10
git diff --stat HEAD~5..HEAD 2>/dev/null

# Estado /pm flow (si aplica)
test -f docs/product/BACKLOG-TLDR.md && cat docs/product/BACKLOG-TLDR.md
ls docs/product/stories/ 2>/dev/null | head -20

# Active stories con state intermedio
for cp in docs/product/stories/*/checkpoint.md; do
  STATE=$(grep -E "^state:" "$cp" 2>/dev/null | head -1 | awk '{print $2}')
  case "$STATE" in
    refining|refined|ready|developing|developed|reviewing|blocked)
      echo "$(dirname $cp | xargs basename) → $STATE"
      ;;
  esac
done
```

Compone resumen en memoria:
- Commits this session (con SHAs)
- Files modified pero NO commiteados (si hay)
- Active stories con state intermedio
- Blocker/in-progress thread (qué quedó "next action")
- Bootstrap prompt sugerido para próxima session

### Step 2 — Spawn Haiku worker

```
Agent({
  description: "Write handoff doc for session close",
  subagent_type: "general-purpose",
  model: "haiku",
  prompt: "<prompt template below>"
})
```

### Prompt template (verbatim — orchestrator fills `<...>` placeholders)

```
Write a session handoff doc to <HANDOFF_PATH>.

## Context (provided by orchestrator — use verbatim, no embellish)

### Commits this session
<list of {sha} {subject} from git log filtered to this session>

### Uncommitted state
<git status --short output OR "tree clean">

### Active stories (state intermedio)
<list of story-id → state extracted from checkpoint.md scan>

### Blocker / in-progress thread
<orchestrator-provided 1-3 lines: what was being worked, what next step>

### Bootstrap prompt for next session
<orchestrator-provided ready-to-paste prompt user puede copy/pegar para resume>

## Output structure (write to <HANDOFF_PATH>)

```markdown
# Session Handoff — <ISO-timestamp UTC>

## Commits this session
<bullet list with SHA short + conventional commit subject>

## Tree state
<clean | uncommitted files list>

## Active work threads
<bullet per story-id with state + 1-line context>

## Blocker / next action
<verbatim orchestrator description>

## Bootstrap prompt (paste this into next session)
\```
<orchestrator-provided prompt>
\```

## References
- Latest BACKLOG-TLDR: `docs/product/BACKLOG-TLDR.md`
- Story checkpoints: `docs/product/stories/{id}/checkpoint.md`
- Process learnings: `docs/process/learnings.md`
```

## Steps to execute
1. Create file at <HANDOFF_PATH> using Write tool
2. Insert content above using verbatim placeholders provided
3. Print path: `Wrote <HANDOFF_PATH>`

Do NOT add commentary. Do NOT modify the orchestrator-provided sections. You are a template-fill worker.

Last line MUST be: `done -> <HANDOFF_PATH>` or `failed -> <reason>`
```

### Step 3 — Process Haiku result

- `done -> <path>` → orchestrator prints path al user + sugiere "ya podés cerrar la session"
- `failed -> <reason>` → orchestrator inspecciona y reintenta, o fallback manual a Write tool

### Step 4 — (Optional) commit handoff doc

Si user quiere commitear el handoff (raro, normalmente queda untracked):

```
Use /commit-push skill con files=[<HANDOFF_PATH>]
```

## Anti-patterns

- ❌ Opus orchestrator escribe handoff doc directo (waste — Haiku cubre template-fill)
- ❌ Spawn sin pre-audit `git log` + checkpoint scan (Haiku no tiene contexto session)
- ❌ Bootstrap prompt vago tipo "continúa lo que hacías" — debe ser ready-to-paste con story-id concreto
- ❌ Auto-commit handoff sin user confirmation (handoffs/ default untracked)
- ❌ Multiple handoffs same minute → orchestrator agrega `-N` suffix manual

## Output format (Opus → user)

```
✅ Handoff doc generado: docs/product/handoffs/2026-05-09-1430.md

Próxima session: leé el handoff doc PRIMERO, luego paste el bootstrap prompt.
```

## Referencias

- `.claude/rules/git-haiku-delegation.md` — Haiku delegation pattern
- `.claude/skills/cierra-limpio/SKILL.md` — clean close sin handoff (commit pendientes only)
- `docs/process/parallel-sessions-protocol.md` — multi-session WIP rules
