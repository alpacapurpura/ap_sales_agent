---
phase: 7
slug: stage-3-oportunidad
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (inside Docker container) |
| **Config file** | `backend/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | OPO-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_opportunity_metrics.py -x` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | OPO-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_shopify_webhook.py -x` | ❌ W0 | ⬜ pending |
| 07-01-03 | 01 | 1 | OPO-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/scheduling/test_appointment_events.py -x` | ❌ W0 | ⬜ pending |
| 07-01-04 | 01 | 1 | OPO-05 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_bottleneck_detection.py -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | OPO-01 | manual | Visual verification | -- | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/analytics/test_opportunity_metrics.py` — stubs for OPO-02, OPO-05
- [ ] `tests/modules/connections/test_shopify_webhook.py` — stubs for OPO-03
- [ ] `tests/modules/scheduling/test_appointment_events.py` — stubs for OPO-04

*Existing infrastructure covers test framework setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OpportunityDetail panel renders two groups (Web Transactional Friction, High-Ticket Qualification) | OPO-01 | Visual layout verification | Navigate to Growth Studio > Opportunity stage; confirm two group sections render with correct headers |
| Bottleneck indicator visual flag | OPO-05 | Visual styling verification | Trigger high abandon ratio in test data; confirm red/warning indicator appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
