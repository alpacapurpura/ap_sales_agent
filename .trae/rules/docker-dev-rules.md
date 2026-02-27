# Docker Rules (Dev & Prod)
CRITICAL: If the current environment (Development or Production) is unknown, ALWAYS ASK THE USER before running commands.

## Development (docker-compose.yml)
| Svc | Service | Container | Port |
| API | api_dev | visionarias_brain_dev | 8000 |
| Admin | admin_dashboard_dev | visionarias_admin_dev | 8501 |
| Client | client_dashboard_dev | visionarias_client_dev | 3000 |
| WA | whatsapp_engine | visionarias_whatsapp | 8080 |
| Infra | redis, qdrant, postgres | visionarias_* | Exposed |

## Production (docker-compose.prod.yml)
| Svc | Service | Container | Access |
| API | backend | visionarias_brain | Traefik/Internal |
| Admin | admin | visionarias_admin | SSH Tunnel (8501) |
| Client | frontend | visionarias_client | Traefik/Public |
| Infra | redis, qdrant, postgres | visionarias_* | Internal Only |