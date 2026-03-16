---
status: resolved
trigger: "Docker Compose solution not fully starting - some containers stuck in Created state, one unhealthy"
created: 2026-03-15T00:00:00Z
updated: 2026-03-15T00:00:00Z
---

## Current Focus

hypothesis: All three root causes identified and fixed.
test: Full docker compose up --profile extended; all containers checked for healthy status
expecting: All containers running and healthy
next_action: Archive session

## Symptoms

expected: All Docker Compose containers should be running and healthy after `docker compose up -d`
actual: visionarias_scheduler and visionarias_worker stuck in "Created" state. visionarias_admin_dev running but "unhealthy".
errors: No error logs from scheduler/worker (they never started). Admin dashboard shows Streamlit on 8501 but health check fails.
reproduction: Run `docker compose up -d` from /home/chris/AISALESHT
started: Current state right now

## Eliminated

- hypothesis: scheduler/worker stuck in Created because arq not in image
  evidence: After removing stale `image:` refs from docker-compose.yml and forcing fresh build, containers now START. The arq issue is fully resolved.
  timestamp: 2026-03-16T00:00:00Z

## Evidence

- timestamp: 2026-03-15T17:27:00Z
  checked: docker inspect visionarias_scheduler error
  found: "exec: arq: executable file not found in $PATH" -- container fails at OCI runtime create
  implication: The image used by scheduler/worker doesn't have arq installed

- timestamp: 2026-03-15T17:27:00Z
  checked: docker images for visionarias_brain_dev vs aisalesht-api_dev
  found: visionarias_brain_dev:latest is 3 weeks old (efdea8b2c280), aisalesht-api_dev:latest is 5 days old (b8f78f4f2a7c). arq==0.27.0 is in requirements.txt.
  implication: scheduler/worker use stale image that predates arq being added to requirements

- timestamp: 2026-03-16T00:00:00Z
  checked: scheduler/worker crash logs after docker-compose.yml fix
  found: "pydantic_core.ValidationError: 1 validation error for Settings — API_URL Field required". API_URL is declared as a required str (no default) in config.py line 80, but is absent from .env. The stale image previously prevented Python from even loading, so this config error was never reached.
  implication: Need to add API_URL to .env. Usage in codebase is for webhook URL construction (e.g. https://dev-api.nicolify.com/api/v1/whatsapp/webhook/...). Correct value: https://dev-api.nicolify.com

- timestamp: 2026-03-15T17:27:00Z
  checked: docker inspect visionarias_admin_dev healthcheck
  found: Healthcheck curls localhost:8000/health but admin runs Streamlit on port 8501. Healthcheck is inherited from Dockerfile.
  implication: Admin needs healthcheck override in docker-compose.yml to check port 8501

## Resolution

root_cause: |
  THREE issues compounding:
  1. Scheduler/Worker: `image: visionarias_brain_dev:latest` resolved to a 3-week-old cached image without `arq`. Containers failed at OCI runtime create with "exec: arq: executable file not found in $PATH".
  2. Admin Dashboard: Dockerfile HEALTHCHECK curled port 8000 (API) but Streamlit runs on 8501. No override in docker-compose.yml.
  3. API_URL missing from .env: pydantic Settings declares API_URL as required str (no default). Never surfaced before because the stale image crashed before Python even loaded. All services (api_dev, scheduler, worker) failed to import settings.
fix: |
  1. docker-compose.yml: Replaced `image: visionarias_brain_dev:latest` with `build: ./backend` on scheduler, worker, admin_dashboard_dev.
  2. docker-compose.yml: Added healthcheck override for admin_dashboard_dev → curl http://localhost:8501/_stcore/health.
  3. docker-compose.yml: Added healthcheck overrides for scheduler/worker → python redis ping (not HTTP).
  4. backend/src/modules/analytics/workers/settings.py: SchedulerSettings no longer inherits WorkerSettings; all required attrs duplicated directly (arq's get_kwargs uses __dict__, not inherited attrs).
  5. .env: Added API_URL=https://dev-api.nicolify.com (public URL for webhook construction).
verification: |
  All containers verified healthy:
  - visionarias_brain_dev: Up (healthy)
  - visionarias_worker: Up (healthy)
  - visionarias_scheduler: Up (healthy)
  - visionarias_admin_dev: Up (healthy)
  Scheduler logs confirm: Redis connected to redis:6379, 7 functions registered (4 tasks + 3 cron jobs).
files_changed: [docker-compose.yml, backend/src/modules/analytics/workers/settings.py, .env]
