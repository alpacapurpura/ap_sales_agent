# Technical Debt Ledger

Centralised log of known technical debt and deferred work across Nicolify.
Each file documents what was intentionally left undone, what was discovered
mid-flight, and what the follow-up actually needs.

## Conventions

- **One file per session / initiative.** Filenames follow
  `YYYY-MM-DD-<kebab-case-summary>.md` so they sort chronologically.
- **Inside each file, items are categorised** by severity: `P0` (blocks
  production), `P1` (blocks UX or data correctness), `P2` (quality of
  life), `P3` (nice-to-have).
- Every item has: **What**, **Why deferred**, **Effort estimate**, and
  pointer to the commit / file where the deferred seam lives.
- If an item lands, **move it to `resolved/`** (create on demand) with a
  resolution commit reference instead of deleting — keeps archaeology
  cheap.

## Current files

| File | Topic | Last updated |
|------|-------|--------------|
| [2026-04-17-offer-editions-session.md](2026-04-17-offer-editions-session.md) | Offer Editions UI revamp (Phases 5-9e) — backend enrollments, sales agent tools, public URLs, editions rail, interview date block, Ventas tab | 2026-04-17 |

## Working with this ledger

1. **Before starting a new feature:** skim relevant files here to know
   what you are or aren't inheriting.
2. **During work:** update or resolve items in-place.
3. **End of session:** if you added new debt, append to the current
   session's file or create a new one.
4. **Never delete an entry outright** — move it to `resolved/` so later
   sessions understand the project history.

## What does NOT belong here

- Regular backlog items (product features). Those live in Linear / the
  roadmap.
- Bugs reproducible in prod — those go to Sentry / an issue tracker.
- Code style nitpicks covered by ESLint / ruff — those are enforced by
  the linter, not tracked here.

Only *intentionally deferred work* that a future session needs to decide
on belongs here.
