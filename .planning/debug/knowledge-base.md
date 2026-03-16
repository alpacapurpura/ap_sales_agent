# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## docker-compose-containers-not-starting — Containers stuck in Created/unhealthy due to stale image, wrong healthcheck port, and missing .env var
- **Date:** 2026-03-16
- **Error patterns:** Created state, unhealthy, arq executable not found, exec arq, ValidationError, API_URL Field required, curl Failed to connect port 8000, healthcheck, SchedulerSettings, WorkerSettings, image stale, visionarias_brain_dev
- **Root cause:** (1) scheduler/worker used stale `image: visionarias_brain_dev:latest` (3 weeks old, no arq). (2) admin_dashboard_dev healthcheck curled port 8000 but Streamlit runs on 8501. (3) API_URL missing from .env — pydantic Settings has it as required with no default; was hidden by stale image crash. (4) SchedulerSettings inherited WorkerSettings but arq's get_kwargs uses __dict__ (not inherited attrs), so redis_settings was invisible.
- **Fix:** Remove stale `image:` refs from docker-compose.yml (use `build:` instead). Add healthcheck override for admin on port 8501. Add healthcheck override for scheduler/worker using redis ping. Duplicate all attrs directly on SchedulerSettings (no inheritance). Add API_URL to .env.
- **Files changed:** docker-compose.yml, backend/src/modules/analytics/workers/settings.py, .env
---

