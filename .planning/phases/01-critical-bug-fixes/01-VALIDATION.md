---
phase: 1
slug: critical-bug-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0.0 + pytest-asyncio >=0.23.5 |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/connections/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | BUGFIX-01 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_meta_api_version.py -x` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | BUGFIX-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_meta_tenant_isolation.py::test_sequential -x` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | BUGFIX-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_meta_tenant_isolation.py::test_concurrent -x` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | BUGFIX-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/connections/test_ga4_data_client.py -x` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | BUGFIX-03 | integration | `docker exec -t visionarias_brain_dev pytest tests/integration/test_ga4_live.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/connections/test_meta_api_version.py` — stubs for BUGFIX-01 (API version constant, URL construction)
- [ ] `tests/modules/connections/test_meta_tenant_isolation.py` — stubs for BUGFIX-02 (sequential + concurrent isolation)
- [ ] `tests/modules/connections/test_ga4_data_client.py` — stubs for BUGFIX-03 (runReport wrapper, mocked)
- [ ] `tests/integration/test_ga4_live.py` — stubs for BUGFIX-03 (live GA4 integration, skipped in CI)
- [ ] `tests/modules/connections/conftest.py` — shared fixtures (mock credentials, adapter factories)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Re-authorization prompt for existing GA4 tenants | BUGFIX-03 | Requires real OAuth flow with existing tenant | 1. Connect GA4 with existing tenant 2. Verify `analytics.readonly` scope prompt 3. Confirm `runReport()` works after re-auth |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
