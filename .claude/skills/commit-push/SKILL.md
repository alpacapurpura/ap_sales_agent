---
name: commit-push
description: "Stage + commit + push delegation a Haiku worker (token-cheap pattern, origen 2026-05-09). Orchestrator (Opus) prepara plan; Haiku ejecuta git workflow con guardrails verbatim. Activa: '/commit-push', 'commitea y sube', 'commit haiku', 'commit y push', 'commit + push'."
allowed-tools: Read, Bash, Agent
model: opus
---

# /commit-push — Haiku-delegated git workflow

> SSoT guardrails: `.claude/rules/git-haiku-delegation.md`
> SSoT git fundamentals: `.claude/rules/git-safety.md` + `.claude/rules/parallel-safety.md`

## Cuándo usar

- Multi-file commit + push (default case)
- "commitea y sube" / "commit + push" del user
- Después de implementar feature/fix multi-file en orchestrator session

## Cuándo NO usar

- Single-file conversational `git commit -am "<msg>"` < 200 tokens (Bash directo OK)
- Conflict resolution / merge / rebase / cherry-pick (orchestrator caso a caso)
- User pidió `git revert` / `--force` / destructivo (NUNCA, sin importar delegación)

## Steps

### Step 1 — Pre-spawn audit (Opus orchestrator)

```bash
git status --short            # categorizar files MINE vs OTHERS
git branch --show-current     # MUST = development
git log --oneline -3          # contexto reciente
```

Categoriza output `git status --short`:
- Files con prefix `M ` / ` M` / `??` que TÚ tocaste this session → `MINE` list
- Files con prefix de otras sessions (deletions ajenas, untracked ajenos) → `OTHERS` list (leave alone)

Reject pre-spawn si:
- Branch ≠ `development` → STOP, switch first
- Hay match `.env*` / `credentials*` / `*.pem` en MINE list → STOP, escalate Chris (security)
- Tree limpio (nada para commitear) → STOP, no spawn

### Step 2 — Compose commit message (Opus)

Conventional Commits format:
- Subject: `<type>(<scope>): <desc>` (≤ 70 chars). Types: feat/fix/refactor/docs/test/chore/perf/ci.
- Body: 1-3 lines explican "why", no "what". Referencias tickets/origen si aplica.
- Footer: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`

### Step 3 — Spawn Haiku worker

```
Agent({
  description: "Commit + push <short-summary>",
  subagent_type: "general-purpose",
  model: "haiku",
  prompt: "<prompt template below>"
})
```

### Prompt template (verbatim — no improvise)

```
You are a git workflow worker. Perform commit + push for Nicolify project.

## Working directory
/home/chris/AISALESHT (current branch: development)

## Critical safety rules (HARD — origen .claude/rules/git-haiku-delegation.md)
- NEVER `git add .` / `git add -A` / `git add -u` — parallel sessions WIP en tree
- Stage ONLY by exact filename (lista provista abajo)
- NEVER `git commit --no-verify` — pre-commit hook mandatory
- NEVER `git pull` / `git fetch && merge` — banned per parallel-safety.md
- NEVER `git push --force` / `--force-with-lease` — banned
- NEVER `git revert` sin aprobación explícita
- Si `git push origin development` fails non-fast-forward → STOP, report. NO pull.
- Si pre-commit hook fails → fix and create NEW commit (never `--amend` pushed commits)
- Working branch = `development`. NUNCA push a `main`.

## Files to stage (exact names — these belong to MY session)
<exact list from MINE>

## Files to LEAVE ALONE (parallel sessions WIP — verify intactos post-stage)
<exact list from OTHERS — copy git status output verbatim>

## Commit message (HEREDOC required)
```
<full conventional commit message including body + Co-Authored-By footer>
```

## Steps to execute
1. `git status --short` — verify state
2. `git add <space-separated MINE files>` — stage by exact name (NEVER `add .`)
3. `git status --short` — verify OTHERS files still unstaged + intact
4. Commit using HEREDOC syntax with message above
5. `git push origin development`
6. `git log --oneline -2` — confirm commit landed
7. Report final commit SHA + push result

Last line MUST be: `done -> <commit-sha>` or `failed -> <reason>`
```

### Step 4 — Process Haiku result

Haiku worker last-line:
- `done -> <sha>` → orchestrator reporta success al user (1 line)
- `failed -> <reason>` → orchestrator lee reason:
  - `non-fast-forward` → STOP, escalate Chris (no pull, no force)
  - `pre-commit hook <details>` → inspect hook output, fix issue, re-spawn Haiku con same plan
  - `secret detected` → STOP escalate Chris (security)
  - `branch mismatch` → switch branch, re-spawn

## Anti-patterns

- ❌ Opus invoca `git commit -m` directo cuando MINE list ≥ 3 files (debió delegar)
- ❌ Spawn Haiku sin guardrails verbatim
- ❌ Pasar "auto-generate commit message" a Haiku (Opus tiene contexto semantic, Haiku no)
- ❌ Spawn `subagent_type: builder-*` para git (wrong type — esos son code Opus)
- ❌ Permitir Haiku ejecutar `git pull` / `--force` / `--no-verify` bajo cualquier excusa

## Output format (Opus orchestrator a user)

Después delegación exitosa:
```
✅ Commit `<sha>` pushed a origin/development.
- <N> files staged: <comma list>
- Pre-commit hook: passed
- Tree: clean
```

Después fail:
```
❌ Commit failed: <reason verbatim from Haiku>
Próximo paso: <orchestrator decision based on failure mode>
```

## Referencias

- `.claude/rules/git-haiku-delegation.md` — pattern + cost saving + guardrails completos
- `.claude/rules/git-safety.md` — git fundamentals
- `.claude/rules/parallel-safety.md` — M1-M8 multi-session protection
