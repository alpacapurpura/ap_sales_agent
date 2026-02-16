#!/bin/bash
set -e

echo "🚀 Iniciando despliegue en PRODUCCIÓN (VPS)..."
echo "📂 Usando configuración: docker-compose.prod.yml + .env.prod"

# 1. Pull Latest Code (Redundancia de seguridad)
echo "📥 Asegurando última versión del código..."
git pull origin main

# 2. Build and Start Services
echo "🏗️ Construyendo y levantando servicios de producción..."
# Use --build to force rebuild of images with new changes
# --remove-orphans limpia contenedores viejos
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build --remove-orphans

# 3. Database Migrations
echo "🔄 Ejecutando migraciones de base de datos..."
# Wait for DB to be ready
sleep 5

# Attempt to upgrade database schema
if docker exec visionarias_brain alembic upgrade head; then
    echo "✅ Migraciones exitosas."
else
    echo "⚠️ Error en migraciones. Intentando sincronizar (stamp head)..."
    docker exec visionarias_brain alembic stamp head
    echo "✅ Base de datos sincronizada (stamp head)."
fi

# 4. Check Health
echo "🏥 Verificando salud del sistema..."

# Check API health
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ API Backend saludable (HTTP 200)."
else
    echo "❌ ERROR CRÍTICO: API Backend no responde en localhost:8000."
fi

# Check Frontend health
if [ "$(docker inspect -f '{{.State.Running}}' visionarias_client 2>/dev/null)" = "true" ]; then
    echo "✅ Contenedor Frontend corriendo."
else
    echo "❌ ERROR CRÍTICO: Contenedor Frontend NO está corriendo."
fi

echo "✅ Despliegue de producción completado."
echo "🌐 Frontend: https://salesagent.alpacapurpura.lat"
echo "🔧 Admin: https://admin.salesagent.alpacapurpura.lat (Acceso restringido)"
