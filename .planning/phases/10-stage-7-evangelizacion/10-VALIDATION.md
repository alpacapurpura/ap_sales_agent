---
phase: 10
slug: stage-7-evangelizacion
status: draft
nyquist_compliant: true
wave_0_complete: true
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
| 10-01-00 | 01 | 1 | EVA-02,03,04 | stub | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_evangelization_metrics.py backend/tests/modules/analytics/test_k_factor.py backend/tests/modules/crm/test_nps_service.py backend/tests/modules/crm/test_referral_service.py -x -q` | Wave 0 task creates them | ⬜ pending |
| 10-01-01 | 01 | 1 | EVA-02 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/crm/test_referral_service.py -x` | Created by 10-01-00 | ⬜ pending |
| 10-01-02 | 01 | 1 | EVA-03 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_k_factor.py -x` | Created by 10-01-00 | ⬜ pending |
| 10-01-03 | 01 | 1 | EVA-04 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/crm/test_nps_service.py -x` | Created by 10-01-00 | ⬜ pending |
| 10-02-01 | 02 | 2 | EVA-01 | unit | `docker exec -t visionarias_brain_dev pytest backend/tests/modules/analytics/test_evangelization_metrics.py -x` | Created by 10-01-00 | ⬜ pending |
| 10-03-01 | 03 | 3 | EVA-01 | integration | Frontend manual verification (component renders) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `backend/tests/modules/analytics/test_evangelization_metrics.py` — created by Plan 10-01 Task 0
- [x] `backend/tests/modules/analytics/test_k_factor.py` — created by Plan 10-01 Task 0
- [x] `backend/tests/modules/crm/test_nps_service.py` — created by Plan 10-01 Task 0
- [x] `backend/tests/modules/crm/test_referral_service.py` — created by Plan 10-01 Task 0

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Evangelization panel renders with correct groups and KPIs | EVA-01 | Frontend component rendering requires browser | Load Growth Studio > navigate to Evangelization panel > verify both Referidos and Reputacion groups render with correct KPIs |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
