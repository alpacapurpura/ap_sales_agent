.PHONY: dev install-front fix-front fix-permissions

# Iniciar entorno de desarrollo
dev:
	docker compose --profile development up -d --build

# Instalar paquete en Frontend (Host + Docker)
# Uso: make install-front p=nombre-del-paquete
install-front:
	@if [ -z "$(p)" ]; then echo "Error: Define el paquete con p=nombre"; exit 1; fi
	@echo "📦 Instalando $(p) en Host..."
	cd frontend && npm install $(p)
	@echo "🐳 Sincronizando $(p) en Docker..."
	docker compose exec client_dashboard npm install $(p)
	@echo "✅ Listo! Dependencia sincronizada."

# Reparar dependencias (Sincronización Total)
fix-front:
	@echo "🔧 Reparando dependencias en Host..."
	cd frontend && npm install
	@echo "🐳 Reparando dependencias en Docker..."
	docker compose exec client_dashboard npm install
	@echo "✅ Entorno Frontend sincronizado correctamente."

# Corregir permisos de archivos (Usuario Host)
fix-permissions:
	@echo "🔐 Corrigiendo permisos de archivos (Docker -> Host)..."
	docker compose run --rm --entrypoint "chown -R 1000:1000 /app" client_dashboard
	@echo "✅ Permisos corregidos. Ahora puedes ejecutar make fix-front"
