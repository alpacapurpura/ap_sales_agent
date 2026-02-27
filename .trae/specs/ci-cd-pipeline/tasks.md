# Tasks

- [x] Task 1: Create GitHub Actions Workflow
  - [x] SubTask 1.1: Define build job with Docker layer caching (GHA cache)
  - [x] SubTask 1.2: Define push step to GHCR with proper tagging
  - [x] SubTask 1.3: Define deploy job using `appleboy/ssh-action`

- [x] Task 2: Create Production Docker Compose File
  - [x] SubTask 2.1: Create `docker-compose.prod.yml` based on existing config
  - [x] SubTask 2.2: Update services to use GHCR images
  - [x] SubTask 2.3: Remove host port bindings (8000:8000, 3000:3000) and rely on Traefik
  - [x] SubTask 2.4: Configure `restart: always` and `healthcheck` for zero-downtime readiness

- [x] Task 3: Create Deployment Script
  - [x] SubTask 3.1: Create `scripts/deploy.sh`
  - [x] SubTask 3.2: Implement secret injection logic (create .env from args/env)
  - [x] SubTask 3.3: Implement migration execution (`alembic upgrade head`)
  - [x] SubTask 3.4: Implement rolling update logic (`docker compose up -d --no-recreate` strategy or scaling)

- [x] Task 4: Validate and Finalize
  - [x] SubTask 4.1: Review files against requirements
  - [x] SubTask 4.2: Ensure all secrets are documented for the user to add to GitHub
