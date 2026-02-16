# Development Map & Rules

## Structure
/backend: Python/FastAPI. Src: /backend/src.
/frontend: Next.js/React. Src: /frontend/src.
/data: Persistence (DB, Vector, Cache).

## Routing & Network
Local Dev: http://localhost:3000 (Frontend) -> http://localhost:8000 (Backend).
Cloudflare Dev Tunnel: https://laptopchris.alpacapurpura.lat (Exposes Local Dev).
Production (VPS): https://salesagent.alpacapurpura.lat (No Cloudflare).

## Data Flow
1. Browser requests hit API directly (localhost:8000 in Dev, salesagent.alpacapurpura.lat/api in Prod).
2. SSR/Server Actions hit container name (visionarias_brain_dev).
3. External tools (Telegram/Google) hit Public URL (Tunnel in Dev, VPS IP/Domain in Prod).

## Critical Config
Files:
  - Development: `docker-compose.yml` + `.env`
  - Production: `docker-compose.prod.yml` + `.env.prod`

.env: Master config (Dev).
.env.prod: Master config (Prod).

NEXT_PUBLIC_API_URL: 
  - Dev: http://localhost:8000
  - Prod: https://apisalesagent.alpacapurpura.lat
INTERNAL_API_URL: 
  - Dev: http://visionarias_brain_dev:8000
  - Prod: http://backend:8000

## Rules
OS: Ubuntu/WSL. Use sudo.
Python: Strict typing. Always run 'ruff check backend/src --fix' after edits.
Frontend: Mobile-first. Run 'npm run lint:fix' to clean code.
Docker: Check health after up.