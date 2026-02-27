# Backend Permissions Audit Spec

## Why
The user plans a complete restructuring of the `backend` directory. Current permission checks reveal `root`-owned files (e.g., in `.ruff_cache`), which will block autonomous file operations (move, delete, edit). This spec ensures the agent (running as `chris` in WSL) has full read/write/execute permissions across the entire backend codebase to prevent errors during the upcoming restructure.

## What Changes
- **Identify User Context**: Confirm the user under which the Trae AI agent operates (verified as `chris`).
- **Change Ownership**: Recursively change ownership of `/home/chris/AISALESHT/backend` to the agent's user (`chris`) to eliminate `root` ownership locks and ensure full control.
- **Fix Permissions**: Ensure directories are executable/writable and files are readable/writable for the agent's user.
- **Validation**: Verify `mkdir`, `mv`, `rm`, `ruff`, and `npx` execution within the backend context specifically as the agent user.

## Impact
- Affected specs: None directly, but prerequisites for all future backend work.
- Affected code: No code changes, only file system metadata (permissions/ownership).

## ADDED Requirements
### Requirement: Agent User Context Verification
The system SHALL identify the current user executing commands (Trae AI agent context) and ensure permissions are aligned to this user.

#### Scenario: User Check
- **WHEN** agent runs `whoami`
- **THEN** the output identifies the user (e.g., `chris`) to be granted permissions.

### Requirement: Full User Ownership
The system SHALL ensure all files and directories within `backend/` are owned by the identified agent user (`chris:chris`).

#### Scenario: Success case
- **WHEN** agent attempts to move or delete a file previously owned by root (e.g., in `.ruff_cache`)
- **THEN** the operation succeeds without `Permission denied` errors.

### Requirement: Tool Execution
The system SHALL ensure standard development tools (`ruff`, `npx`) can be executed by the agent in the `backend/` directory.

#### Scenario: Tool check
- **WHEN** agent runs `ruff check .` or `npx --version`
- **THEN** the command executes successfully (exit code 0 or expected tool output).
