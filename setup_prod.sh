#!/bin/bash
# setup_prod.sh

# 1. Definir directorio raíz de producción
PROJECT_ROOT="/opt/ap_sales_agent"

echo "🚀 Iniciando configuración de directorios en $PROJECT_ROOT..."

# 2. Crear estructura de carpetas faltante
# Frontend
mkdir -p "$PROJECT_ROOT/frontend/public"      # Crítico: Faltaba y rompió el build
mkdir -p "$PROJECT_ROOT/frontend/src"         # Estructura base

# Backend
mkdir -p "$PROJECT_ROOT/backend/src"

# Data & Persistencia (Volúmenes Host)
mkdir -p "$PROJECT_ROOT/data/postgres_data"
mkdir -p "$PROJECT_ROOT/data/redis_data"
mkdir -p "$PROJECT_ROOT/data/qdrant_data"
mkdir -p "$PROJECT_ROOT/data/whatsapp_data"

# Cachés (Requieren permisos especiales)
mkdir -p "$PROJECT_ROOT/data/model_cache"

# 3. Ajustar Permisos (chmod 777 para evitar problemas de UID/GID en volúmenes montados)
echo "🔒 Ajustando permisos de volúmenes compartidos..."
chmod -R 777 "$PROJECT_ROOT/data/model_cache"
chmod -R 777 "$PROJECT_ROOT/data/whatsapp_data" # A veces necesario para Evolution API

echo "✅ Estructura de directorios lista en $PROJECT_ROOT"
