.PHONY: all dev dev-core dev-extended build-core build-extended stats-core prod stop stop-dev stop-prod logs logs-dev logs-prod setup fix-permissions install-front fix-front tooling-up tooling-down npm vitest pytest lint ruff pytest-cov vitest-cov e2e e2e-smoke e2e-ui e2e-report shopify-config-dev shopify-config-prod shopify-config-status test-mode dev-mode audit audit-backend audit-frontend arch-test

# Variables
DOCKER_COMPOSE = docker compose
DOCKER_COMPOSE_DEV = $(DOCKER_COMPOSE) -f docker-compose.yml --env-file .env
DOCKER_COMPOSE_PROD = $(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod
DOCKER_COMPOSE_TOOLING = $(DOCKER_COMPOSE_DEV) --profile tooling
DOCKER_COMPOSE_DEV_SEQ = COMPOSE_PARALLEL_LIMIT=1 $(DOCKER_COMPOSE_DEV)
USER_ID := $(shell id -u)
GROUP_ID := $(shell id -g)

# --- Main Commands ---

# Iniciar entorno de Desarrollo
dev:
	$(MAKE) dev-core

dev-core:
	$(DOCKER_COMPOSE_DEV) up -d api_dev client_dashboard_dev redis qdrant postgres

dev-extended:
	$(DOCKER_COMPOSE_DEV) --profile extended up -d

build-core:
	$(DOCKER_COMPOSE_DEV_SEQ) build api_dev client_dashboard_dev

build-extended:
	$(DOCKER_COMPOSE_DEV_SEQ) --profile extended build admin_dashboard_dev scheduler worker

stats-core:
	docker stats --no-stream visionarias_brain_dev visionarias_client_dev visionarias_postgres visionarias_redis visionarias_qdrant

# Test mode: stop non-essential containers to free ~190MB RAM + CPU
test-mode:
	@echo "Stopping non-essential containers for test runs..."
	-docker stop cloudflare-tunnel visionarias_qdrant 2>/dev/null
	@echo "Stopped. Run 'make dev-mode' to restore."

# Dev mode: restart all containers after test-mode
dev-mode:
	@echo "Restoring all containers..."
	-docker start cloudflare-tunnel visionarias_qdrant 2>/dev/null
	@echo "All containers running."

# Iniciar entorno de Producción (Usa .env.prod)
prod:
	$(DOCKER_COMPOSE_PROD) up -d --build

# Detener todos los contenedores
stop:
	$(DOCKER_COMPOSE_DEV) down
	$(DOCKER_COMPOSE_PROD) down

stop-dev:
	$(DOCKER_COMPOSE_DEV) down

stop-prod:
	$(DOCKER_COMPOSE_PROD) down

# Ver logs (sigue el log)
logs:
	$(DOCKER_COMPOSE_DEV) logs -f

logs-dev:
	$(DOCKER_COMPOSE_DEV) logs -f

logs-prod:
	$(DOCKER_COMPOSE_PROD) logs -f

# --- Setup & Maintenance ---

# Crear carpetas necesarias con permisos de usuario (Ejecutar ANTES de iniciar Docker)
setup:
	@echo "📂 Creando estructura de directorios..."
	mkdir -p data/postgres_data
	mkdir -p data/redis_data
	mkdir -p data/qdrant_data
	mkdir -p data/model_cache
	mkdir -p frontend/node_modules
	mkdir -p backend/model_cache
	@echo "✅ Directorios creados correctamente. Listo para 'make dev' o 'make prod'."

# Reparar permisos (Frontend y Backend)
# Útil si ves errores de 'Permission denied' o candados en tus archivos
fix-permissions:
	@echo "🔐 Corrigiendo permisos de archivos (Docker -> Host)..."
	# Fix Frontend (node_modules, .next) - Usamos la imagen de dev
	$(DOCKER_COMPOSE_DEV) run --rm --entrypoint "chown -R $(USER_ID):$(GROUP_ID) /app" client_dashboard_dev
	# Fix Backend (pycache, logs) - Usamos la imagen de dev
	$(DOCKER_COMPOSE_DEV) run --rm --entrypoint "chown -R $(USER_ID):$(GROUP_ID) /app" api_dev
	@echo "✅ Permisos corregidos. Ahora eres dueño de tus archivos."

# --- Frontend Helpers ---

# Instalar paquete: make install-front p=axios
install-front:
	@if [ -z "$(p)" ]; then echo "Error: Define el paquete con p=nombre"; exit 1; fi
	@echo "🐳 Instalando $(p) en Docker..."
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm install $(p)
	@echo "✅ Dependencia instalada."

# Sincronizar node_modules (si alguien más cambió package.json)
fix-front:
	@echo "🐳 Reparando dependencias Frontend en Docker..."
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm ci
	@echo "✅ Entorno Frontend sincronizado correctamente."

tooling-up:
	$(DOCKER_COMPOSE_TOOLING) up -d frontend_tooling backend_tooling

tooling-down:
	$(DOCKER_COMPOSE_TOOLING) down --remove-orphans

npm:
	@if [ -z "$(cmd)" ]; then echo "Error: Define el comando con cmd='...'. Ejemplo: make npm cmd='install axios'"; exit 1; fi
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm $(cmd)

vitest:
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm run test -- $(args)

pytest:
	$(DOCKER_COMPOSE_TOOLING) run --rm backend_tooling pytest $(args)

lint:
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm run lint
	$(DOCKER_COMPOSE_TOOLING) run --rm backend_tooling ruff check src

ruff:
	$(DOCKER_COMPOSE_TOOLING) run --rm backend_tooling ruff check src $(args)

pytest-cov:
	$(DOCKER_COMPOSE_TOOLING) run --rm backend_tooling pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q $(args)

arch-test:
	docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v"

vitest-cov:
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npx vitest run --coverage $(args)

# --- E2E Testing (Playwright) ---
# Generate a fresh Clerk testing token for all workers via env var
CLERK_SK = $(shell grep '^CLERK_SECRET_KEY=' .env | cut -d'=' -f2)
CLERK_TT = $(shell curl -s -X POST "https://api.clerk.com/v1/testing_tokens" -H "Authorization: Bearer $(CLERK_SK)" | python3 -c "import sys,json;print(json.load(sys.stdin).get('token',''))")
DOCKER_COMPOSE_E2E = CLERK_TESTING_TOKEN=$(CLERK_TT) $(DOCKER_COMPOSE_DEV) --profile e2e

e2e:
	$(DOCKER_COMPOSE_E2E) run --rm --no-deps e2e_runner npx playwright test $(args)

e2e-smoke:
	$(DOCKER_COMPOSE_E2E) run --rm --no-deps e2e_runner npx playwright test --grep @smoke $(args)

e2e-ui:
	$(DOCKER_COMPOSE_E2E) run --rm -p 9323:9323 e2e_runner npx playwright test --ui --ui-host 0.0.0.0 --ui-port 9323

e2e-report:
	$(DOCKER_COMPOSE_E2E) run --rm -p 9324:9324 e2e_runner npx playwright show-report --host 0.0.0.0 --port 9324

shopify-config-dev:
	cd shopify_app && npx shopify app config use shopify.app.dev.toml

shopify-config-prod:
	cd shopify_app && npx shopify app config use shopify.app.prod.toml

shopify-config-status:
	cd shopify_app && grep -E "^(name|application_url|client_id)" shopify.app.toml

# --- Dependency Audit ---
audit:
	$(DOCKER_COMPOSE_TOOLING) run --rm backend_tooling pip-audit --strict --desc
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm audit --audit-level=high

audit-backend:
	$(DOCKER_COMPOSE_TOOLING) run --rm backend_tooling pip-audit --strict --desc

audit-frontend:
	$(DOCKER_COMPOSE_TOOLING) run --rm frontend_tooling npm audit --audit-level=high
