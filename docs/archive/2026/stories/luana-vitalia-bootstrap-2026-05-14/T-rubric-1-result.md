# T-rubric-1 Result

**Ticket:** `T-rubric-1` — vertical-medical-fidelity rubric MD v1 + 6 NEW personas YAML archetype-aware
**State:** developed (build phase complete, tests-passing — awaiting auditor)
**Closed:** 2026-05-14 UTC
**Iter:** 1 (single-shot GREEN)
**Validators:** V-AE-20 + V-AE-21 GREEN

## Summary

Authored vertical-medical-fidelity rubric MD v1 (5 weighted assertions A1-A5 production-critical
safety bar 0.85) + 6 NEW vitalia archetype-aware personas (1 happy + 2 nurture + 3 adversarial)
+ 2 NEW arch fitness gates (39 tests total) + filter-based scope update to AISALESHT
existing cement test (preserves Story C 15-cement byte-equal).

Spec compliance: D5 (5-assertion weighted formula) + D6 (rubric_version=1 cement) cementados
en frontmatter + body inline + arch fitness gate sum check.

## Files (artifacts)

### Rubric MD (NEW v1)

| Path | Purpose |
|---|---|
| `/home/chris/AISALESHT/docs/specs/rubrics/vertical-medical-fidelity.md` | Rubric MD v1 — frontmatter (id/version=1/applies_to/modules/verticals/threshold_default=0.85/ssot/owner_story) + 5 assertions A1-A5 weighted (0.30/0.25/0.20/0.15/0.10 = 1.00) + scoring formula + auto-fail triggers + pass^k thresholds + cache invalidation rule + out of scope + calibration + story chain + histórico v1 |

### Personas YAML (6 NEW)

| Path | persona_kind | tenant_slug | dialect_code | archetype | Purpose |
|---|---|---|---|---|---|
| `/home/chris/AISALESHT/docs/specs/personas/archetype-aware/patient-anxious-dental-ar.yaml` | nurture | aurora-dental-ar | es-AR | medicina_dental | Aurora voice voseo + booking happy + consent capture (línea 2 magic comment voseo-allowed) |
| `/home/chris/AISALESHT/docs/specs/personas/archetype-aware/patient-depressed-psych-cl.yaml` | happy | mindful-santiago-cl | es-CL | psicologia | Mindful voice tuteo neutro chileno + orientativa booking + followup D5 |
| `/home/chris/AISALESHT/docs/specs/personas/archetype-aware/patient-unresponsive-followup-mx.yaml` | nurture | sanare-latam-mx | es-MX | psicologia_psiquiatria | D5/D14 escalation paths + paused_awaiting_clinic flow (no responde a primer ping) |
| `/home/chris/AISALESHT/docs/specs/personas/archetype-aware/patient-adversarial-diagnosis-mx.yaml` | adversarial | sanare-latam-mx | es-MX | psicologia_psiquiatria | medical_safety_no_diagnosis guardrail + safety escalation + emergency referral (6 objection variants) |
| `/home/chris/AISALESHT/docs/specs/personas/archetype-aware/patient-prompt-injection-attempt.yaml` | adversarial | any | es-MX | none | prompt_injection_block guardrail + audit_log + no system prompt leak (7 multi-vector attack patterns) |
| `/home/chris/AISALESHT/docs/specs/personas/archetype-aware/patient-medication-recommendation-mx.yaml` | adversarial | sanare-latam-mx | es-MX | psiquiatria | medical_safety_no_prescription guardrail + REQUIRED DISCLAIMER chunk forced retrieval (6 medication topic objections) |

### Architecture fitness gates (2 NEW)

| Path | Tests | Purpose |
|---|---|---|
| `/home/chris/luana-platform/vitalia/backend/tests/architecture/test_vitalia_rubric_md_v1_schema.py` | 18 | Frontmatter v1 schema + 5 assertions A1-A5 + weight sum 1.00 + scoring formula + threshold 0.85 + cache invalidation rule + pass^k thresholds documented |
| `/home/chris/luana-platform/vitalia/backend/tests/architecture/test_vitalia_personas_yaml_completeness.py` | 21 | 6-file count + filename frozen set + schema_version=2 + persona_kind matrix (1+2+3) + tenant_slug ∈ vitalia 4-tenant set + archetype ∈ vitalia 4-archetype set + dialect per file + bloom_stages + persona_gym_axes + voseo magic comment AR + story_origin + required fields + non-empty content fields |

### Cross-cutting (1 modified)

| Path | Change |
|---|---|
| `/home/chris/AISALESHT/backend/tests/architecture/test_personas_yaml_completeness.py` | Filter `patient-*.yaml` (vitalia) from Story C cement scope via `_VITALIA_PERSONA_BASENAME_PREFIX = "patient-"` predicate. Preserves Story C 15-cement byte-equal for original Story C personas. |

## Validators mapping

| Validator | Test path | Status |
|---|---|---|
| V-AE-20 (6 NEW personas YAML schema valid + voseo magic comment AR) | `vitalia/backend/tests/architecture/test_vitalia_personas_yaml_completeness.py` | ✅ 21/21 PASS |
| V-AE-21 (vertical-medical-fidelity.md v1 frontmatter + 5 assertions + scoring formula) | `vitalia/backend/tests/architecture/test_vitalia_rubric_md_v1_schema.py` | ✅ 18/18 PASS |

## Acceptance

- [x] **A1**: Rubric MD v1 schema valid (frontmatter + 5 assertions + scoring) — pytest GREEN.
- [x] **A2**: 6 personas YAML completeness + voseo magic comment AR personas — pytest GREEN.

## Quality gates

- [x] Ruff check: 3/3 files clean
- [x] Ruff format: 3/3 files clean (auto-formatted to canonical)
- [x] Voseo regex sweep: rubric MD clean. AR persona has magic comment línea 2. 5 non-AR personas voseo-clean.
- [x] R3 downstream regression: AISALESHT existing test still 19/19 PASS post filter update (Story C cement byte-equal preserved).

## Run command (re-verify)

```bash
cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest \
  tests/architecture/test_vitalia_rubric_md_v1_schema.py \
  tests/architecture/test_vitalia_personas_yaml_completeness.py \
  -v --tb=short
```

Output: `39 passed in 0.21s`.

## Decisions confirmed at runtime

- **D5** (5-assertion weighted scoring formula): A1 (0.30) + A2 (0.25) + A3 (0.20) + A4 (0.15) + A5 (0.10) = 1.00. Cementado en `vertical-medical-fidelity.md` frontmatter (`threshold_default: 0.85`) + body inline `(weight 0.XX, ...)` per assertion + arch fitness gate `test_vitalia_rubric_assertion_weights_sum_to_1_00`.
- **D6** (rubric_version=1 cement): `version: 1` en frontmatter + body "Cache invalidation" section explica triggers que requieren bump + arch fitness gate `test_vitalia_rubric_frontmatter_version_is_1`.

## Downstream blocks (per ticket spec)

- **T-eval-1** (grader runtime) — UNBLOCKED. Grader implementa MAJ-EVAL state machine reuse Story E pattern + judge prompts especializados per assertion A1-A5 vertical-medical-fidelity. Consume rubric MD + 6 personas authored aquí.

## State

- Builder phase: `tests-passing`
- Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict per R30 enforcement 2026-05-05).

done -> docs/product/stories/luana-vitalia-bootstrap/T-rubric-1-result.md
