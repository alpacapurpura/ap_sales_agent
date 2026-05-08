# T-2 Implementation Log
# Story: sales-agent-personas-instrumented-runtime
# Ticket: T-2 — 15 archetype-aware personas YAML + 5 LEGACY moved + arch fitness gate

## Summary

T-2 completed. All deliverables implemented and validators GREEN.

## Skills Consulted

| Skill | Reason | Decision |
|---|---|---|
| `backend-expert` | Arch fitness gate pattern + ratchet pattern | Used `pytestmark = pytest.mark.no_eval`, empty allowlist shrink-only pattern; `frozenset` for all constant sets |
| `tessl__pytest-api-testing` | Static file test structure | Static filesystem tests with no DB/LLM; `_load_yaml_files` helper for shared file parsing |
| `tessl__fastapi` | N/A (no routes in T-2) | Confirmed T-2 is pure YAML + arch gate (no FastAPI surface) |

## Step 0 — Default-flip detection

No `core/config.py` defaults touched. N/A.

## Files Created

### docs/specs/personas/archetype-aware/ (15 new files)

| File | persona_kind | tenant_slug | dialect_code |
|---|---|---|---|
| lead-frio-impaciente-pe.yaml | happy | tenant_coach_lat | es-PE |
| pregunton-comparador-pe.yaml | nurture | tenant_coach_lat | es-PE |
| tire-kicker-pdf-only-pe.yaml | unqualified | tenant_coach_lat | es-PE |
| paciente-dudosa-mx.yaml | happy | tenant_medicina_estetica | es-MX |
| pregunton-side-effects-mx.yaml | nurture | tenant_medicina_estetica | es-MX |
| wrong-treatment-cirugia-mayor-mx.yaml | unqualified | tenant_medicina_estetica | es-MX |
| referido-calido-co.yaml | happy | tenant_clinica_dental | es-CO |
| pregunton-financiamiento-co.yaml | nurture | tenant_clinica_dental | es-CO |
| emergencia-dolor-no-target-co.yaml | unqualified | tenant_clinica_dental | es-CO |
| ceo-b2b-escala-ar.yaml | happy | tenant_agencia_growth_video | es-AR |
| pregunton-comparador-3-agencias-ar.yaml | nurture | tenant_agencia_growth_video | es-AR |
| pre-pmf-zero-revenue-ar.yaml | unqualified | tenant_agencia_growth_video | es-AR |
| cto-enterprise-419.yaml | happy | tenant_agencia_automatizacion_ia | es-419 |
| pregunton-tech-stack-419.yaml | nurture | tenant_agencia_automatizacion_ia | es-419 |
| solo-founder-no-team-419.yaml | unqualified | tenant_agencia_automatizacion_ia | es-419 |

All 3 es-AR files have `# voseo-allowed: archetype-aware AR persona Story C` on line 2
(valid YAML comment; passes pre-commit hook regex `#\s*voseo-allowed([: \t]|$)`).

### docs/specs/personas/_legacy/ (5 moved via git mv)

- lead-frio-impaciente.yaml
- lead-tibio-dudoso.yaml
- lead-caliente-ready.yaml
- tenant-experto-saturado.yaml
- tenant-novato-tech.yaml

### backend/tests/architecture/test_personas_yaml_completeness.py (NEW arch gate)

19 test functions enforcing:
1. `archetype-aware/` directory exists
2. `_legacy/` directory exists
3. Count = 15 in archetype-aware/
4. Count = 5 in _legacy/
5. schema_version == 2 per file
6. persona_kind in 6-value canonical set
7. tenant_slug in 5 valid Story A slugs
8. archetype in 5 valid archetypes
9. dialect_code strict match vs ARCHETYPE_DIALECT_MAP[tenant_slug]
10. bloom_stages subset of canonical 4
11. persona_gym_axes subset of canonical 5
12. es-AR files have voseo magic comment on line 2
13. 3 kinds per tenant (3x5 matrix D14)
14. Required top-level fields (14 fields)
15. Required metadata fields (5 fields)
16. traits/pain_points/objections non-empty lists
17. initial_message non-empty string
18. legacy filenames exact match (frozenset of 5)
19. YAML parses as dict (no malformed files)

## Issues Found and Fixed

### Issue 1 — Lint: ambiguous multiplication sign
`×` (MULTIPLICATION SIGN U+00D7) in docstrings/comments triggers `RUF002`/`RUF003`.
Fix: replaced all `×` with `x` (ASCII) in test file.

### Issue 2 — Lint: f-string without placeholder
`f"3-kinds × 5-tenants matrix (D14) violations:\n"` had `f` prefix with no `{}`.
Fix: removed `f` prefix, kept as plain string.

### Issue 3 — Format
ruff format reformatted 1 file. Applied formatter output.

## Validators Run

| Validator | Status | Notes |
|---|---|---|
| be_lint (`ruff check`) | PASS | 0 errors after 2 fix iterations |
| be_format (`ruff format --check`) | PASS | Applied formatter |
| arch_personas_yaml_completeness | PASS | 19/19 tests |
| full arch fitness (`tests/architecture/`) | PASS | 980/980 tests |
| A1 shell count | PASS | 15 archetype-aware + 5 legacy |

## Cross-module reads

None. T-2 is self-contained (YAML + static arch gate).

## Notes

- `voseo-allowed` magic comment uses `#` YAML comment syntax (not HTML `<!--`).
  HTML comment `<!-- ... -->` is not valid YAML and would cause parse errors.
- Arch gate path resolution: `parents[2]` = `backend/`, `parent` = repo root.
  `_ARCHETYPE_AWARE_DIR` = `<repo_root>/docs/specs/personas/archetype-aware/`.
- `pytestmark = pytest.mark.no_eval` — no LLM invocation in this gate.
- story_origin: `C-T-2` on all 15 archetype-aware files.
