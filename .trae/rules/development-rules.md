## Structure
/backend: Python/FastAPI. Src: /backend/src.
/frontend: Next.js/React. Src: /frontend/src.
/data: Persistence (DB, Vector, Cache).
## Routing & Network
Local Dev: http://localhost:3000 (Frontend) -> http://localhost:8000 (Backend).
Cloudflare Dev Tunnel: https://laptopchris.alpacapurpura.lat (Exposes Local Dev).
Production (VPS): https://salesagent.alpacapurpura.lat (No Cloudflare).
## Critical Config
Files:
  - Development: `docker-compose.yml` + `.env`
  - Production: `docker-compose.prod.yml` + `.env.prod`
NEXT_PUBLIC_API_URL: 
  - Dev: http://localhost:8000
  - Prod: https://apisalesagent.alpacapurpura.lat
INTERNAL_API_URL: 
  - Dev: http://visionarias_brain_dev:8000
  - Prod: http://backend:8000
## Entorno de Desarrollo
OS: Ubuntu/WSL. Use sudo.