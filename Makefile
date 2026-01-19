.PHONY: all dev prod stop logs setup fix-permissions install-front fix-front

# Variables
DOCKER_COMPOSE = docker compose
USER_ID := $(shell id -u)
GROUP_ID := $(shell id -g)

# --- Main Commands ---

# Iniciar entorno de Desarrollo
dev:
	$(DOCKER_COMPOSE) --profile development up -d --build

# Iniciar entorno de Producción (Usa .env.prod)
prod:
	$(DOCKER_COMPOSE) --env-file .env --profile production up -d --build

# Detener todos los contenedores
stop:
	$(DOCKER_COMPOSE) --profile development --profile production down

# Ver logs (sigue el log)
logs:
	$(DOCKER_COMPOSE) logs -f

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
	$(DOCKER_COMPOSE) run --rm --entrypoint "chown -R $(USER_ID):$(GROUP_ID) /app" client_dashboard_dev
	# Fix Backend (pycache, logs) - Usamos la imagen de dev
	$(DOCKER_COMPOSE) run --rm --entrypoint "chown -R $(USER_ID):$(GROUP_ID) /app" api_dev
	@echo "✅ Permisos corregidos. Ahora eres dueño de tus archivos."

# --- Frontend Helpers ---

# Instalar paquete: make install-front p=axios
install-front:
	@if [ -z "$(p)" ]; then echo "Error: Define el paquete con p=nombre"; exit 1; fi
	@echo "📦 Instalando $(p) en Host..."
	cd frontend && npm install $(p)
	@echo "🐳 Sincronizando $(p) en Docker..."
	$(DOCKER_COMPOSE) exec client_dashboard_dev npm install $(p)
	@echo "✅ Listo! Dependencia sincronizada."

# Sincronizar node_modules (si alguien más cambió package.json)
fix-front:
	@echo "🔧 Reparando dependencias en Host..."
	cd frontend && npm install
	@echo "🐳 Reparando dependencias en Docker..."
	$(DOCKER_COMPOSE) exec client_dashboard_dev npm install
	@echo "✅ Entorno Frontend sincronizado correctamente."
