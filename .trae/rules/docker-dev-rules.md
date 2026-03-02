# Docker Rules (Dev & Prod)
CRITICAL: If the current environment (Development or Production) is unknown, ALWAYS ASK THE USER before running commands.

## Development (docker-compose.yml profile development)
| Svc | Service | Container | Port |
| API | api_dev | visionarias_brain_dev | 8000 |
| Admin | admin_dashboard_dev | visionarias_admin_dev | 8501 |
| Client | client_dashboard_dev | visionarias_client_dev | 3000 |
| WA | whatsapp_engine | visionarias_whatsapp | 8080 |
| Infra | redis, qdrant, postgres | visionarias_* | Exposed |

## Networking & Variables
- **INTERNAL_API_URL**: Used for Server-Side communication (SSR/Server Actions) within the Docker network.
  - Value: `http://visionarias_brain_dev:8000` (Dev) or `http://backend:8000` (Prod).
- **NEXT_PUBLIC_API_URL**: Used for Client-Side communication (Browser -> API).
  - Value: `http://localhost:8000` (Local), Cloudflare URL (Tunnel), or Domain (Prod).|