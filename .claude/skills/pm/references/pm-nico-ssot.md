# PM-Nico SSoT — DEPRECATED reference

> **🛑 DEPRECATED 2026-05-06 (Wave 2 pm-redesign).**
>
> `docs/pm-nico/` no longer exists. New SSoT functional lives in `docs/product/`:
> - `BACKLOG.{yaml,md}` (auto-gen via `scripts/generate_backlog.py` — pre-commit hook Section 6 R33 keeps fresh)
> - `ideas-pool.yaml` — ideas + validated entries with OST inline
> - `outcomes/{outcome-id}.md` — epics narrativa + frontmatter
> - `stories/{story-id}/` — flat folder per active story (checkpoint.md + 01-spec.md + 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml + T-{n}-* artifacts)
> - `capabilities/{module}/{cap}.yaml` — durable behavior post-merge (R32 `scripts/reconcile_capabilities.py` keeps statuses fresh)
> - `modules/{module}.md` — module-level state functional (frontmatter + narrativa unique + auto-list marker)
>
> **For paradigm details:** `docs/process/pm-redesign-2026-05.md`.

## Replacement workflow (was: pm-nico/current-state update)

When session modifies user-facing functionality:

1. **During build** — no manual update needed (autonomous loop)
2. **At merge** (Conv 3 / `/pm` Step) —
   - Update `docs/product/capabilities/{m}/{cap}.yaml` with embedded scenarios + test_coverage paths
   - `python3 scripts/reconcile_capabilities.py` — recompute status derivado
   - `python3 scripts/generate_backlog.py` — refresh BACKLOG.{yaml,md}
   - Update `docs/product/modules/{m}.md` (only if narrativa changes — auto-list refresh marker)
   - Archive story folder to `docs/archive/{year}/stories/{story-id}/`
   - Append entry en `docs/process/learnings.md` si decisión cardinal

See `.claude/skills/pm/SKILL.md` § "Capability promotion (al merge)" for full workflow.
