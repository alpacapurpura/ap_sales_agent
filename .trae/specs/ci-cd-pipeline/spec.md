# CI/CD Pipeline & Production Hardening Spec

## Why
Current manual deployment is unsustainable, error-prone, and causes downtime. The goal is to automate the build, test, and deploy process using GitHub Actions, while improving security (secrets management), performance (caching), and reliability (zero-downtime strategies).

## What Changes
- **New GitHub Workflow**: `.github/workflows/ci-cd.yml` to handle build, test, push to GHCR, and deploy via SSH.
- **New Production Compose**: `docker-compose.prod.yml` optimized for production (no host port binding, uses GHCR images, external network).
- **Deployment Script**: `scripts/deploy.sh` to handle secrets injection, migration execution, and zero-downtime rolling updates.
- **Dockerfile Optimization**: Ensure multi-stage builds are fully leveraged and layer caching is active in CI.
- **Secret Management**: Transition from manual `.env` file management to GitHub Secrets injection during deployment.

## Impact
- **Affected specs**: Deployment process.
- **Affected code**: 
    - `.github/workflows/ci-cd.yml` (New)
    - `docker-compose.prod.yml` (New)
    - `scripts/deploy.sh` (New)
    - `backend/Dockerfile` (Minor tweak if needed for cache)
    - `frontend/Dockerfile` (Minor tweak if needed for cache)

## ADDED Requirements
### Requirement: Automated CI/CD Pipeline
The system SHALL automatically build and deploy changes to the production environment upon push to the `main` branch.

#### Scenario: Successful Deployment
- **WHEN** a developer pushes code to `main`
- **THEN** GitHub Actions triggers the pipeline
- **AND** builds Docker images with layer caching
- **AND** pushes images to GHCR
- **AND** executes the deployment script on the production server via SSH
- **AND** the server pulls new images
- **AND** runs database migrations
- **AND** performs a rolling update to minimize downtime.

### Requirement: Secure Secret Management
The system SHALL NOT store secrets in the repository or rely on a permanently insecure `.env` file on the server. Secrets SHALL be injected from GitHub Secrets during deployment.

### Requirement: Zero-Downtime Deployment
The deployment process SHALL minimize downtime by using pre-pulling and rolling updates (or blue-green if feasible) for the application services.

## MODIFIED Requirements
### Requirement: Docker Compose Configuration
**Reason**: To support production-grade deployment with external networks and no host port binding.
**Migration**: Use `docker-compose.prod.yml` for production deployments instead of `docker-compose.yml`.
