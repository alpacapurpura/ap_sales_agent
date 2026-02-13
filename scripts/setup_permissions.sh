#!/bin/bash
set -e

echo "🚀 Starting permissions setup for production..."

# 1. Create necessary directories
echo "📂 Creating data directories..."
mkdir -p data/postgres_data
mkdir -p data/redis_data
mkdir -p data/qdrant_data
mkdir -p data/model_cache
mkdir -p data/whatsapp_data
mkdir -p data/static

# 2. Sync initial static files (if any) from codebase to data volume
# This ensures that if we mount data/static over /app/static, we don't lose the initial assets
if [ -d "backend/static" ]; then
    echo "🔄 Syncing initial static files to data/static..."
    # Copy only if destination doesn't exist (no clobber)
    cp -rn backend/static/* data/static/ || true
fi

# 3. Set permissions
# We set 777 for data directories to ensure Docker containers with different UIDs can write.
# This handles the postgres/redis/appuser permission issues commonly seen in Docker.
echo "🔐 Setting permissions..."
chmod -R 777 data/

# 4. Create external network if it doesn't exist
NETWORK_NAME="web_gateway"
if [ -z $(docker network ls --filter name=^${NETWORK_NAME}$ --format="{{ .Name }}") ]; then
     echo "🌐 Creating Docker network: ${NETWORK_NAME}"
     docker network create ${NETWORK_NAME}
else
     echo "✅ Docker network ${NETWORK_NAME} already exists."
fi

echo "✅ Setup complete! You can now run 'docker compose --profile production up -d --build' or use scripts/deploy_prod.sh"
