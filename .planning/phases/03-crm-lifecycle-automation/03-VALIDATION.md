---
phase: 3
slug: crm-lifecycle-automation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | `backend/pyproject.toml` (ruff only) — no pytest config, uses defaults |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/crm/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | CRM-01 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_lifecycle_scoring.py -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | CRM-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_sale_lifecycle.py -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | CRM-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_sale_lifecycle.py -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | CRM-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_inactivity_detection.py -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | CRM-05 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/crm/test_churn_detection.py -x` | ❌ W0 | ⬜ pending |
| EventBus | 01 | 1 | — | unit | `docker exec -t visionarias_brain_dev pytest tests/shared/test_event_bus.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/crm/__init__.py` — package init
- [ ] `tests/modules/crm/conftest.py` — CRM-specific fixtures (sample profiles, events, sales)
- [ ] `tests/modules/crm/test_lifecycle_scoring.py` — stubs for CRM-01
- [ ] `tests/modules/crm/test_sale_lifecycle.py` — stubs for CRM-02, CRM-03
- [ ] `tests/modules/crm/test_inactivity_detection.py` — stubs for CRM-04
- [ ] `tests/modules/crm/test_churn_detection.py` — stubs for CRM-05
- [ ] `tests/shared/__init__.py` — package init
- [ ] `tests/shared/test_event_bus.py` — EventBus unit tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Cancellation webhook end-to-end | CRM-05 | Shopify webhook requires live connection | Trigger cancellation via manual API endpoint, verify lifecycle_stage = CHURNED |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
