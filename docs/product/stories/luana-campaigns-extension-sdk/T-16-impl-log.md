# T-16 Implementation Log — docs/extension-points.md complete

**Story:** luana-campaigns-extension-sdk
**Batch:** E
**Date:** 2026-05-12
**Builder:** builder-backend Sonnet

## Summary

Wrote `luana-platform/docs/extension-points.md` with §1-§5 per spec. Includes
CC-1..CC-5 narrative, EP-1..EP-5 per-vertical examples (Vitalia/Comunify/Lupulo),
EP-6..EP-18 backlog signatures, vertical-agent recipe with "NO EP-19" literal + statement,
and cross-brand learning principle. Spanish neutro LatAm throughout (no voseo).

## File created

- `docs/extension-points.md` — ~480 lines

## Sections implemented

| Section | Validator | Status |
|---|---|---|
| §1 SDK overview + CC-1..CC-5 principles | V-F-docs-1 | GREEN |
| §2 EP-1..EP-5 critical with Vitalia/Comunify/Lupulo examples | V-F-docs-1 | GREEN |
| §3 EP-6..EP-18 backlog signatures + per-vertical examples | V-F-docs-1 | GREEN |
| §4 Recipe: Build vertical agent on luana-core (Vitalia treatment-agent) | V-F-docs-1 | GREEN |
| §5 Cross-brand learning principle | V-F-docs-1 | GREEN |

## Key invariants in doc

- "NO EP-19" literal string present (case-insensitive — V-F-docs-1 enforces)
- "Vertical agent ES un APP del brand, NO un EP del core." statement present
- `apps/vitalia/agents/treatment_agent/` code skeleton consuming 6 luana-core packages
- All 5 vertical identifiers present: vitalia, comunify, lupulo + brand examples
- Spanish neutro throughout — pre-commit hook did not flag voseo

## Test validation

`test_docs_extension_points_completeness.py` parses MD headers + literal strings.
All assertions GREEN (committed in T-17 batch).

## luana-platform commit

`325209e` — `docs(luana-platform): docs/extension-points.md §1-§5 + vertical-agent-recipe + per-vertical examples`

## Skills Consulted

- `backend-expert`: documentation conventions
- `.claude/rules/spanish-text.md`: neutro LatAm, no voseo imperatives
