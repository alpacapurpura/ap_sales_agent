# Deployment Organization Spec

## Why
Currently, deployment scripts and configurations are scattered in the root directory or generic `scripts/` folder, making it difficult to understand the deployment process, manage different strategies (Local vs GitHub Actions), and maintain documentation. The user wants a centralized, organized structure to manage deployments easily.

## What Changes
- **New Directory Structure**: Create a `deployment/` directory (added to `.gitignore` except for documentation/scripts that should be tracked, or fully tracked if it contains non-sensitive data. *Correction*: User asked for it to be in `.gitignore`, but typically deployment scripts should be versioned. I will assume the user wants the *output* or *sensitive configs* ignored, but the scripts themselves versioned. However, if the user explicitly said "que este en el gitignore", I will follow that, but I will advise that scripts *should* be versioned. I will add `deployment/` to `.gitignore` but maybe suggest keeping a template. *Wait*, if it's in gitignore, I can't push it to the repo. I will interpret "que este en el gitignore" as "que lo que se genere o secretos estén ignorados", but the scripts must be in the repo to be useful for the team. *Refinement*: The user said "crea una carpeta llamada despliegue, que este en el gitignore". I will add `despliegue/` to `.gitignore`. This implies these are local convenience scripts/configs for the current developer).
- **Subdirectories**:
  - `despliegue/local/`: Contains the local deployment script (`deploy_local.sh`) and a `README.md` with step-by-step instructions.
  - `despliegue/github_actions/`: Contains the GitHub Actions workflow file (copy/reference), the remote deployment script (`deploy.sh`), and a `README.md` explaining how to set up secrets and monitor the workflow.
- **Monitoring Tools**: The scripts should provide feedback (logs) and the documentation should explain how to monitor (e.g., `docker logs`, GitHub Actions tab).

## Impact
- **Affected specs**: None directly, but reorganizes existing deployment assets.
- **Affected code**:
  - `scripts/deploy.sh` -> moved to `despliegue/github_actions/deploy.sh`
  - `scripts/deploy_local.sh` -> moved to `despliegue/local/deploy_local.sh`
  - `.gitignore`: Added `despliegue/`
  - `.github/workflows/ci-cd.yml`: Updated to point to new script location if necessary (or we keep the source of truth in `.github` and just document it in `despliegue`).

## ADDED Requirements
### Requirement: Centralized Deployment Folder
The system SHALL have a `despliegue/` directory containing all deployment-related materials.

### Requirement: Local Deployment Submodule
The `despliegue/local/` directory SHALL contain:
- The script to deploy from the local machine (`deploy_local.sh`).
- A `README.md` explaining prerequisites (SSH keys, .env.prod) and execution steps.

### Requirement: GitHub Actions Submodule
The `despliegue/github_actions/` directory SHALL contain:
- A copy or reference to the `deploy.sh` used by the runner.
- A `README.md` explaining how to trigger the workflow, set secrets, and monitor progress on GitHub.

### Requirement: Step-by-Step Documentation
Each deployment method SHALL have clear, step-by-step documentation enabling a developer to execute and monitor the deployment.

## MODIFIED Requirements
### Requirement: Script Locations
**Reason**: To declutter the project root and organize by deployment strategy.
**Migration**: Move existing scripts to the new folder structure.
