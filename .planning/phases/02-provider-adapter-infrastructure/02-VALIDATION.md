---
phase: 2
slug: provider-adapter-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0.0 + pytest-asyncio >= 0.23.5 |
| **Config file** | `backend/tests/conftest.py` (exists) |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | INFRA-01 | unit | `pytest tests/modules/analytics/test_provider_adapter.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | INFRA-02 | unit | `pytest tests/modules/analytics/test_connection_port.py -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | INFRA-03 | unit | `pytest tests/modules/analytics/test_metrics_cache.py -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | INFRA-04 | unit | `pytest tests/modules/analytics/test_cost_type.py -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | INFRA-05 | unit+smoke | `pytest tests/modules/analytics/test_channel_fallback.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/analytics/conftest.py` — shared fixtures (mock credentials, test tenant, mock Redis)
- [ ] `tests/modules/analytics/test_provider_adapter.py` — stubs for INFRA-01
- [ ] `tests/modules/analytics/test_connection_port.py` — stubs for INFRA-02
- [ ] `tests/modules/analytics/test_metrics_cache.py` — stubs for INFRA-03
- [ ] `tests/modules/analytics/test_cost_type.py` — stubs for INFRA-04
- [ ] `tests/modules/analytics/test_channel_fallback.py` — stubs for INFRA-05
- [ ] `tests/modules/analytics/test_etl_pipeline.py` — E2E pipeline test with mocked adapters

*Framework install: pytest + pytest-asyncio already in requirements.txt*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Disconnected providers show "Configurar" badge | INFRA-05 | UI visual verification | 1. Seed DB with disconnected channel 2. Navigate to Growth Studio 3. Verify "Configurar" badge appears 4. Verify active channels shown first |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
