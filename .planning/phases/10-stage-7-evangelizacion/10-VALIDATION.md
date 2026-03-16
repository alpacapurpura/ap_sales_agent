---
phase: 10
slug: stage-7-evangelizacion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (inside Docker container) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | EVA-02 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_evangelization_metrics.py -x` | -- Wave 0 | ⬜ pending |
| 10-01-02 | 01 | 1 | EVA-03 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_k_factor.py -x` | -- Wave 0 | ⬜ pending |
| 10-01-03 | 01 | 1 | EVA-04 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/crm/test_nps_service.py -x` | -- Wave 0 | ⬜ pending |
| 10-01-04 | 01 | 1 | EVA-02 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/crm/test_referral_service.py -x` | -- Wave 0 | ⬜ pending |
| 10-02-01 | 02 | 2 | EVA-01 | integration | Frontend manual verification (component renders) | -- Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/modules/analytics/test_evangelization_metrics.py` — stubs for EVA-02, EVA-03
- [ ] `backend/tests/modules/analytics/test_k_factor.py` — stubs for EVA-03
- [ ] `backend/tests/modules/crm/test_nps_service.py` — stubs for EVA-04
- [ ] `backend/tests/modules/crm/test_referral_service.py` — stubs for referral code generation and Shopify extraction

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Evangelization panel renders with correct groups and KPIs | EVA-01 | Frontend component rendering requires browser | Load Growth Studio > navigate to Evangelization panel > verify both Referidos and Reputacion groups render with correct KPIs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
