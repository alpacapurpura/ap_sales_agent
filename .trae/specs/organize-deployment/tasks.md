# Tasks

- [x] Task 1: Create Directory Structure
  - [x] SubTask 1.1: Create `despliegue/` folder
  - [x] SubTask 1.2: Create `despliegue/local/` and `despliegue/github_actions/`
  - [x] SubTask 1.3: Update `.gitignore` to include `despliegue/` (as requested, though I will add a note about versioning)

- [x] Task 2: Migrate Local Deployment
  - [x] SubTask 2.1: Move `scripts/deploy_local.sh` to `despliegue/local/deploy_local.sh`
  - [x] SubTask 2.2: Create `despliegue/local/README.md` with detailed instructions and monitoring steps (how to check logs via SSH)

- [x] Task 3: Migrate GitHub Actions Deployment
  - [x] SubTask 3.1: Copy `scripts/deploy.sh` to `despliegue/github_actions/deploy.sh` (This is the script executed *on* the server)
  - [x] SubTask 3.2: Create `despliegue/github_actions/README.md` explaining the workflow, secrets setup, and how to view logs on GitHub

- [x] Task 4: Cleanup
  - [x] SubTask 4.1: Remove old `scripts/` folder if empty or only containing moved scripts
