# General Development Rules

Environment:
- OS: Ubuntu (WSL). Use sudo for system actions. Password: 20042004i.

Project Routing:
- Backend: /backend directory. Refer to back-*.md rules for Python/FastAPI standards.
- Frontend: /frontend directory. Refer to front-*.md rules for Next.js/React standards.

Core Principles:
- Code-First: The truth is in the code.
- DRY: Extract common logic to shared utilities.
- Strict Typing: Explicit types required. No 'any'.

Workflow:
- Config: Environment variables in .env. Never hardcode secrets.
- Cleanliness: No console.log or print statements in production code.
- Error Handling: Fail fast and explicitly.
