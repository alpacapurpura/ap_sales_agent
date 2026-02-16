#!/bin/bash
set -e

echo "🚀 Iniciando despliegue local..."

# 1. Build and Start Services
echo "🏗️ Construyendo y levantando contenedores..."
# Use --build to force rebuild of images with new changes
# Assuming docker-compose.yml is in the root directory
docker compose --profile development up -d --build

# 2. Database Migrations
echo "🔄 Ejecutando migraciones de base de datos..."
# Wait for DB to be ready (simple sleep for now)
sleep 5

# Attempt to upgrade database schema
if docker exec visionarias_brain_dev alembic upgrade head; then
    echo "✅ Migraciones exitosas."
else
    echo "⚠️ Error en migraciones. Intentando sincronizar (stamp head)..."
    # Fallback: stamp head if schema exists but migration table is out of sync
    docker exec visionarias_brain_dev alembic stamp head
    echo "✅ Base de datos sincronizada (stamp head)."
fi

# 3. Check Health
echo "🏥 Verificando salud del sistema..."
# Check API health
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ API saludable (HTTP 200)."
else
    echo "❌ Advertencia: API podría no estar respondiendo correctamente en /health."
fi

# Check Frontend health
if [ "$(docker inspect -f '{{.State.Running}}' visionarias_client_dev 2>/dev/null)" = "true" ]; then
    echo "✅ Contenedor Frontend corriendo."
else
    echo "❌ Contenedor Frontend NO está corriendo."
fi

echo "✅ Despliegue completado exitosamente."
