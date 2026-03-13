.PHONY: all dev prod stop stop-dev stop-prod logs logs-dev logs-prod setup fix-permissions install-front fix-front shopify-config-dev shopify-config-prod shopify-config-status

# Variables
DOCKER_COMPOSE = docker compose
DOCKER_COMPOSE_DEV = $(DOCKER_COMPOSE) -f docker-compose.yml --env-file .env
DOCKER_COMPOSE_PROD = $(DOCKER_COMPOSE) -f docker-compose.prod.yml --env-file .env.prod
USER_ID := $(shell id -u)
GROUP_ID := $(shell id -g)

# --- Main Commands ---

# Iniciar entorno de Desarrollo
dev:
	$(DOCKER_COMPOSE_DEV) up -d --build

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
	@echo "📦 Instalando $(p) en Host..."
	cd frontend && npm install $(p)
	@echo "🐳 Sincronizando $(p) en Docker..."
	$(DOCKER_COMPOSE_DEV) exec client_dashboard_dev npm install $(p)
	@echo "✅ Listo! Dependencia sincronizada."

# Sincronizar node_modules (si alguien más cambió package.json)
fix-front:
	@echo "🔧 Reparando dependencias en Host..."
	cd frontend && npm install
	@echo "🐳 Reparando dependencias en Docker..."
	$(DOCKER_COMPOSE_DEV) exec client_dashboard_dev npm install
	@echo "✅ Entorno Frontend sincronizado correctamente."

shopify-config-dev:
	cd shopify_app && npx shopify app config use shopify.app.dev.toml

shopify-config-prod:
	cd shopify_app && npx shopify app config use shopify.app.prod.toml

shopify-config-status:
	cd shopify_app && grep -E "^(name|application_url|client_id)" shopify.app.toml
