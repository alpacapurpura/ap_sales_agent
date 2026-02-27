# Tasks
- [x] Task 1: Identify Agent Context
  - [x] SubTask 1.1: Run `whoami` and `id` to confirm the user executing the agent (Trae AI).
  - [x] SubTask 1.2: Record the username (expected: `chris`) for permission assignment.
- [x] Task 2: Fix File System Permissions
  - [x] SubTask 2.1: Recursively change ownership (`chown`) of `/home/chris/AISALESHT/backend` to the identified user (`chris`) using `sudo`.
  - [x] SubTask 2.2: Fix read/write permissions (`chmod`) for the user if restricted (ensure `u+rwx`).
- [x] Task 3: Verify File Operations
  - [x] SubTask 3.1: Create a test directory and file deep in `src/` as the agent user.
  - [x] SubTask 3.2: Move the test file to a different location.
  - [x] SubTask 3.3: Delete the test file and directory.
- [x] Task 4: Verify Tool Execution
  - [x] SubTask 4.1: Run `ruff --version` and a dry-run check.
  - [x] SubTask 4.2: Run `npx --version` to confirm availability.

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 2]
