---
phase: 6
slug: stage-2-nutricion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (inside Docker container) |
| **Config file** | `backend/pyproject.toml` |
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
| 06-01-xx | 01 | 1 | NUT-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_nurture_metrics.py -x` | ❌ W0 | ⬜ pending |
| 06-01-xx | 01 | 1 | NUT-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_retargeting_filter.py -x` | ❌ W0 | ⬜ pending |
| 06-01-xx | 01 | 1 | NUT-04 | integration | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_mailerlite_webhook.py -x` | ❌ W0 | ⬜ pending |
| 06-01-xx | 01 | 1 | NUT-05 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_stage_cost_service.py -x` | ❌ W0 | ⬜ pending |
| 06-02-xx | 02 | 2 | NUT-01 | manual | Manual verification via ENABLE_MOCKS | -- | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/analytics/test_nurture_metrics.py` — stubs for NUT-02 (MQL counting from lifecycle_transitions)
- [ ] `tests/modules/analytics/test_retargeting_filter.py` — stubs for NUT-03 (Custom Audience detection logic)
- [ ] `tests/modules/analytics/test_mailerlite_webhook.py` — stubs for NUT-04 (webhook -> journey_event -> scoring)
- [ ] `tests/modules/analytics/test_stage_cost_service.py` — stubs for NUT-05 (StageCostService calculations)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| NurtureDetail panel renders two groups (Retargeting Omnichannel, Automation) | NUT-01 | Frontend visual rendering with ENABLE_MOCKS | 1. Set ENABLE_MOCKS=true 2. Navigate to Growth Studio 3. Click Nutricion stage 4. Verify two channel groups render with correct headers |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
