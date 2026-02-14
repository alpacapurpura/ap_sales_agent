#!/bin/bash
# Script para actualizar configuración de producción y corregir el bucle de redirección
# Uso: ./deploy_updates.sh

SERVER_IP="161.132.41.191"
SERVER_PORT="22022"
SERVER_USER="root"
SSH_KEY="/home/chris/.ssh/id_rsa"
REMOTE_PATH="/opt/ap_sales_agent"

echo "🚀 Iniciando despliegue de correcciones en $SERVER_IP..."

# 1. Copiar .env.prod al servidor como .env
echo "📦 Actualizando .env en servidor..."
scp -P $SERVER_PORT -i $SSH_KEY .env.prod $SERVER_USER@$SERVER_IP:$REMOTE_PATH/.env

# 2. Copiar next.config.js actualizado
echo "📦 Actualizando configuración de Next.js..."
scp -P $SERVER_PORT -i $SSH_KEY frontend/next.config.js $SERVER_USER@$SERVER_IP:$REMOTE_PATH/frontend/next.config.js

# 3. Ejecutar comandos remotos: Symlinks y Rebuild
echo "🔧 Configurando enlaces simbólicos y reconstruyendo..."
ssh -p $SERVER_PORT -i $SSH_KEY $SERVER_USER@$SERVER_IP "bash -c '
  cd $REMOTE_PATH
  
  # Crear enlaces simbólicos para .env
  echo \"🔗 Creando symlinks de .env...\"
  ln -sf ../.env frontend/.env
  ln -sf ../.env backend/.env
  
  # Reconstruir frontend
  echo \"🔄 Reconstruyendo contenedor de frontend...\"
  docker compose up -d --build client_dashboard_prod
'"

echo "✅ Despliegue completado."
echo "👉 Verifica el acceso en: https://salesagent.alpacapurpura.lat/"
