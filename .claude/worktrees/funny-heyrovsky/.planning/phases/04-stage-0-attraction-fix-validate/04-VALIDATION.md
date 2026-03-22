---
phase: 4
slug: stage-0-attraction-fix-validate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (inside Docker container) |
| **Config file** | `backend/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q` |
| **Full suite command** | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -x -q`
- **After every plan wave:** Run `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green + validation script passes for connected providers
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 0 | ATR-02 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_google_analytics_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 0 | ATR-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_meta_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 0 | ATR-03 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_youtube_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 0 | ATR-03, ATR-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_tiktok_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 0 | ATR-04 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_google_ads_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 0 | ATR-05 | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_crm_internal_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 0 | ALL | unit | `docker exec -t visionarias_brain_dev pytest tests/modules/analytics/test_multi_metric_dto.py -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 3 | ATR-01 | integration | `docker exec -t visionarias_brain_dev python scripts/validate_attraction.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/modules/analytics/test_google_analytics_provider.py` — stubs for ATR-02 (GA4 sessions/users)
- [ ] `tests/modules/analytics/test_meta_provider.py` — stubs for ATR-03, ATR-04 (Instagram organic, Facebook organic, Meta Ads)
- [ ] `tests/modules/analytics/test_youtube_provider.py` — stubs for ATR-03 (YouTube reach/impressions)
- [ ] `tests/modules/analytics/test_tiktok_provider.py` — stubs for ATR-03, ATR-04 (TikTok organic + ads)
- [ ] `tests/modules/analytics/test_google_ads_provider.py` — stubs for ATR-04 (Google Ads clicks/spend)
- [ ] `tests/modules/analytics/test_crm_internal_provider.py` — stubs for ATR-05 (cold contact response rate)
- [ ] `tests/modules/analytics/test_multi_metric_dto.py` — stubs for multi-metric DTO transformation
- [ ] `scripts/validate_attraction.py` — validation script for ATR-01 (ETL vs API comparison)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Attraction metrics match native dashboards | ATR-01 | Requires live provider credentials and dashboard comparison | Connect Visionarias tenant, run ETL, compare values in UI vs provider dashboard within 5% tolerance |
| Frontend renders multi-metric channels | ALL | Visual rendering verification | Navigate to Growth Studio > Attraction, verify each channel row shows correct metric labels and values |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
