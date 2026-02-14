#!/bin/bash
set -e

# ==========================================
# Deployment Script for Production
# ==========================================

echo "🚀 Starting Deployment..."

# 1. Setup Environment Variables
# ------------------------------------------
echo "🔐 Setting up secure environment..."
if [ -z "$PROD_ENV_FILE" ]; then
  echo "❌ Error: PROD_ENV_FILE secret is not set."
  exit 1
fi

# Write .env file securely (chmod 600)
echo "$PROD_ENV_FILE" > .env
chmod 600 .env

# 2. Login to Registry
# ------------------------------------------
echo "🐳 Logging into GitHub Container Registry..."
# Use GITHUB_TOKEN passed from workflow as password
echo "$GHCR_PAT" | docker login ghcr.io -u "$GITHUB_REPOSITORY_OWNER" --password-stdin

# 3. Pull Latest Images
# ------------------------------------------
echo "📥 Pulling latest images..."
# Pre-pulling reduces downtime significantly during restart
docker compose -f docker-compose.prod.yml pull

# 4. Database Migrations
# ------------------------------------------
echo "🔄 Running database migrations..."
# Run migrations in a temporary container. 
# If this fails, the script exits and we don't restart the app.
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 5. Restart Services
# ------------------------------------------
echo "♻️  Updating services..."
# 'up -d' will recreate containers with the new image.
# We use --remove-orphans to clean up any old services.
docker compose -f docker-compose.prod.yml up -d --remove-orphans

# 6. Cleanup
# ------------------------------------------
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment Successful!"
