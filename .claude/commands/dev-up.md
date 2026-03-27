Start Docker dev environment and verify container health.

Steps:
1. Run `docker compose up -d` to start all services
2. Wait 5 seconds for containers to initialize
3. Run `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"` to show container status
4. Check if key containers are healthy:
   - `visionarias_brain_dev` (backend)
   - `visionarias_client_dev` (frontend)
   - `visionarias_postgres` (database)
   - `visionarias_redis` (cache)
5. Report any containers that are not running or unhealthy
