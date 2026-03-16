---
phase: 9
slug: stages-5-6-adoption-expansion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (inside Docker container) |
| **Config file** | backend/pytest.ini or pyproject.toml |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py tests/modules/analytics/test_expansion_metrics.py -x` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py tests/modules/analytics/test_expansion_metrics.py -x`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | ADO-01 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py::test_health_by_offer -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | ADO-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_endpoint.py -x` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | ADO-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py::test_ttv_calculation -x` | ❌ W0 | ⬜ pending |
| 09-01-04 | 01 | 1 | ADO-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_adoption_metrics.py::test_bottleneck_low_health -x` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 1 | EXP-01 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_metrics.py::test_expansion_groups -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | EXP-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_endpoint.py -x` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 1 | EXP-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_metrics.py::test_ltv_average -x` | ❌ W0 | ⬜ pending |
| 09-02-04 | 02 | 1 | EXP-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_expansion_metrics.py::test_churn_rate_bottleneck -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/analytics/test_adoption_metrics.py` — stubs for ADO-01, ADO-03, ADO-04
- [ ] `tests/modules/analytics/test_adoption_endpoint.py` — stubs for ADO-02
- [ ] `tests/modules/analytics/test_expansion_metrics.py` — stubs for EXP-01, EXP-03, EXP-04
- [ ] `tests/modules/analytics/test_expansion_endpoint.py` — stubs for EXP-02
- Existing `conftest.py` with `test_tenant_id`, `sample_offer_id`, `sample_customer_id` fixtures covers shared needs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Adoption health bar visual rendering | ADO-01 | CSS proportional rendering not testable in unit tests | Inspect bar segments in browser: green/yellow proportions match active/inactive ratio |
| Churn group red visual treatment | EXP-04 | Visual styling verification | Inspect churn section has red accent styling in browser |
| Dual currency display formatting | ADO-01, EXP-01 | Visual formatting check | Verify both currencies display correctly on all monetary KPIs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
