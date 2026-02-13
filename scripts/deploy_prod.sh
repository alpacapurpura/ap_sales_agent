#!/bin/bash
set -e

echo "🚀 Starting Production Deployment..."

# 1. Setup Permissions & Network
./scripts/setup_permissions.sh

# 2. Build and Start Containers
echo "🐳 Building and starting containers..."
docker compose --profile production up -d --build

# 3. Post-Deploy Tasks (Migrations)
./scripts/post_deploy.sh

echo "🎉 Deployment Successful!"
