#!/bin/bash
set -e

echo "🚀 Starting post-deployment tasks..."

# 1. Wait for database/API to be ready
echo "⏳ Waiting for API service to initialize (10s)..."
sleep 10

# 2. Run Database Migrations
echo "📦 Running Database Migrations..."
docker compose --profile production exec -T api_prod alembic upgrade head

echo "✅ Post-deployment tasks complete!"
