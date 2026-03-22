---
phase: 5
slug: stage-1-captura
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | `backend/tests/conftest.py` |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CAP-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_capture_metrics.py -x` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | CAP-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_lead_captured_event.py -x` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | CAP-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_capture_cost.py -x` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | CAP-05 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_cal_calculation.py -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | CAP-01 | manual | Manual verification (frontend) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/analytics/test_capture_metrics.py` — stubs for CAP-02 (lead count aggregation by source channel)
- [ ] `tests/modules/analytics/test_lead_captured_event.py` — stubs for CAP-03 (event emission on contact extraction)
- [ ] `tests/modules/analytics/test_capture_cost.py` — stubs for CAP-04 (cost settings CRUD + calculation)
- [ ] `tests/modules/analytics/test_cal_calculation.py` — stubs for CAP-05 (CAL formula)
- [ ] Alembic migration for `channel_cost_settings` table

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Capture detail panel renders two groups (Web Infra / AI Agent) | CAP-01 | Frontend visual layout | Open Growth Studio → Captura detail → verify two distinct channel groups |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
