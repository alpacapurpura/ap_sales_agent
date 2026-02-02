# Development Map & Rules

## Structure
/backend: Python/FastAPI. Src: /backend/src.
/frontend: Next.js/React. Src: /frontend/src.
/data: Persistence (DB, Vector, Cache).

## Routing & Network
Local User: http://salesagent.local (Frontend) -> http://localhost:8000 (Backend).
Docker Internal: Service-to-service via 'visionarias_brain_dev:8000'.
Cloudflare: https://laptopchris.alpacapurpura.lat. USED ONLY for Webhooks/Callbacks.

## Data Flow
1. Browser requests hit localhost:8000 directly.
2. SSR/Server Actions hit container name (visionarias_brain_dev).
3. External tools (Telegram/Google) hit Cloudflare URL -> Tunnel.

## Critical Config
.env: Master config.
NEXT_PUBLIC_API_URL: http://localhost:8000.
INTERNAL_API_URL: http://visionarias_brain_dev:8000.

## Rules
OS: Ubuntu/WSL. Use sudo.
Python: Strict typing. Always run 'ruff check backend/src --fix' after edits.
Frontend: Mobile-first. Run 'npm run lint:fix' to clean code.
Docker: Check health after up.