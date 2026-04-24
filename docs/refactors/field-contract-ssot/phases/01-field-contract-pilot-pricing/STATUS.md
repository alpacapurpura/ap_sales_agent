---
status: done
opened_at: 2026-04-24 15:30
closed_at: 2026-04-24 16:00
baseline_green_commit: 62cfabd1
closing_green_commit: 92523a6e
---

# Fase 01 — Status

Fase abierta. Baseline PRE_FLIGHT capturada:

- BE arch tests: **425 passed** (`cd backend && .venv/bin/pytest tests/architecture/ -x -q`)
- FE arch tests: **37 passed** (`cd frontend && npx vitest run src/__tests__/architecture/`)
- FE tsc: **0 errors**
- Alembic head: `061_offer_narrative_fields`
- `offer_field_paths.json`: **123 paths**
- `KNOWN_UNRESOLVED_PATHS.size`: **59** (cap ADR-007)

## Sub-steps (10 commits atómicos)

| # | Subject | Status | Hash |
|---|---|---|---|
| A | `docs(refactor-field-contract): open fase 01 — SPEC + ACCEPTANCE + ADRs` | done | `fbe4bb08` |
| B | `feat(offer): migration 062 pricing latam columns` | done | `88383918` |
| C | `feat(offer): domain + DTO + model pricing latam` | done | `907e1dcc` |
| D | `feat(offer): FieldContract registry + /field-contract endpoint` | done | `1033d922` |
| E | `feat(offer): extraction wave pricing + prompt + schema` | done | `564b696c` |
| F | `chore(offer): regen field-paths JSON + shrink FE allowlist` | done | `a5b5f3e8` |
| G | `feat(offer-studio): type pricing schema paths against codegen` | done | `4abb34ba` |
| H | `feat(sales-agent): additive pricing block in agent identity prompt` | done | `28efe0e9` |
| I | `test(offer): golden fixture roundtrip pricing latam` | done | `92523a6e` |
| J | `chore(refactor-field-contract): close fase 01` | this commit | tbd |

Ver `SPEC.md` y `ACCEPTANCE.md` para detalle.

## Decisiones abiertas

Ninguna. ADR-008 (wave assignment) y ADR-009 (enum handling) cubiertos
en `DECISIONS.md`.

## Resultado final esperado

- 3 fields nuevos persistidos (`tax_included bool`, `installments_available
  text`, `accepted_payment_providers jsonb NOT NULL DEFAULT '[]'`).
- Extraction wave pricing dedicada (W2 concurrent).
- `offer_field_paths.json`: 123 → **126 paths**.
- `KNOWN_UNRESOLVED_PATHS.size`: 59 → **56**. Cap baja a 56.
- Golden fixture round-trip valida los 3 fields nuevos.
- Sales-agent prompt additive only.
