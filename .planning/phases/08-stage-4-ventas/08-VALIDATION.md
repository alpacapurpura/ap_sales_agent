---
phase: 8
slug: stage-4-ventas
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-16
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), n/a (frontend — no test infrastructure yet) |
| **Config file** | pyproject.toml in backend |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_sales_dto.py backend/tests/modules/analytics/test_offer_read_port.py backend/tests/modules/analytics/test_sales_endpoint.py backend/tests/modules/analytics/test_subscription_split.py backend/tests/modules/analytics/test_cac_calculation.py -x` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/ -x`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-00-01 | 00 | 0 | VEN-01..05 | scaffold | `pytest --collect-only backend/tests/modules/analytics/test_offer_read_port.py backend/tests/modules/analytics/test_sales_dto.py backend/tests/modules/analytics/test_sales_endpoint.py backend/tests/modules/analytics/test_subscription_split.py backend/tests/modules/analytics/test_cac_calculation.py` | Created by 08-00 | ⬜ pending |
| 08-01-01 | 01 | 1 | VEN-01,04 | unit | `pytest backend/tests/modules/analytics/test_offer_read_port.py backend/tests/modules/analytics/test_sales_dto.py backend/tests/modules/analytics/test_subscription_split.py -x` | ✅ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | VEN-02,05 | unit+integration | `pytest backend/tests/modules/analytics/test_sales_endpoint.py backend/tests/modules/analytics/test_cac_calculation.py -x` | ✅ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | VEN-01 | manual | visual inspection | n/a | ⬜ pending |
| 08-02-02 | 02 | 2 | VEN-02 | manual | visual inspection | n/a | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/modules/analytics/test_offer_read_port.py` — stubs for VEN-04 (OfferReadPort ABC + impl) — **created by plan 08-00**
- [x] `backend/tests/modules/analytics/test_sales_dto.py` — stubs for VEN-01 (offer grouping by tier within stage) — **created by plan 08-00**
- [x] `backend/tests/modules/analytics/test_sales_endpoint.py` — stubs for VEN-02 (/metrics/sales endpoint) — **created by plan 08-00**
- [x] `backend/tests/modules/analytics/test_subscription_split.py` — stubs for VEN-03 (new vs renewal split) — **created by plan 08-00**
- [x] `backend/tests/modules/analytics/test_cac_calculation.py` — stubs for VEN-05 (CAC = stages 0-3 costs / CONVERSION) — **created by plan 08-00**
- [x] Test fixtures for SaleModel, ProductModel with tenant_id — **extended in conftest.py by plan 08-00**

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sales detail panel renders offer cards grouped by tier | VEN-01 | Frontend visual layout | Open Growth Studio -> Stage 4, verify cards grouped under Adquisicion/Expansion with tier sub-headers |
| Mini funnel shows Oportunidades -> Ventas conversion | VEN-02 | Frontend visual element | Verify mini funnel displays at top of sales panel |
| CAC asterisk appears when costs incomplete | VEN-05 | UI conditional logic | Remove stage costs, verify asterisk + tooltip appears |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (wave 0 plan 08-00 created)
