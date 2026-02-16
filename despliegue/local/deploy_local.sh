#!/bin/bash
set -e

# ==========================================
# DESPLIEGUE REMOTO (Trigger desde Laptop)
# ==========================================
# Este script se conecta al servidor de producción y ejecuta el protocolo de despliegue seguro.
# ESTÁNDAR: PUSH LOCAL -> PULL SERVIDOR

# Cargar variables de entorno locales si existen (para overrides)
if [ -f .env.prod ]; then
    set -a
    source <(grep -v '^#' .env.prod | sed 's/CORS_ORIGINS=.*//g')
    set +a
fi

# Configuración del Servidor
SERVER_IP="${SERVER_IP:-161.132.41.191}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22022}"
SSH_KEY_PATH="${SSH_KEY_PATH:-/home/chris/.ssh/id_rsa}"
REMOTE_PATH="${REMOTE_PATH:-/opt/ap_sales_agent}"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Iniciando Secuencia de Despliegue a Producción${NC}"
echo "Target: $SERVER_USER@$SERVER_IP:$REMOTE_PATH"

# 1. Verificar Estado Local y Push
echo -e "\n${YELLOW}1. Verificando estado local...${NC}"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}❌ Tienes cambios sin commitear.${NC}"
    echo "   Por favor haz commit de tus cambios antes de desplegar."
    git status -s
    exit 1
fi

echo "Sincronizando rama main local..."
git checkout main
git pull origin main

echo "Subiendo cambios a GitHub..."
git push origin main

# 2. Conexión SSH y Ejecución Remota
echo -e "\n${YELLOW}2. Conectando al servidor para ejecutar despliegue...${NC}"

# Subir .env.prod por seguridad (no se versiona)
echo "📤 Subiendo configuración de secretos (.env.prod)..."
scp -o StrictHostKeyChecking=no -i $SSH_KEY_PATH -P $SERVER_PORT .env.prod $SERVER_USER@$SERVER_IP:$REMOTE_PATH/.env.prod

# Ejecutar comandos remotos
ssh -o StrictHostKeyChecking=no -i $SSH_KEY_PATH -p $SERVER_PORT $SERVER_USER@$SERVER_IP << EOF
    set -e
    
    echo "📍 Conectado a \$(hostname)"
    
    # Asegurar que existe el directorio
    if [ ! -d "$REMOTE_PATH" ]; then
        echo "❌ No encuentro el directorio del proyecto en $REMOTE_PATH"
        exit 1
    fi
    
    cd $REMOTE_PATH
    
    echo "📥 Obteniendo últimos cambios desde GitHub..."
    git reset --hard
    git pull origin main
    
    # Asegurar permisos de ejecución para el script de producción
    chmod +x despliegue/produccion/deploy_prod.sh
    
    # Ejecutar el script de despliegue en producción
    echo "🚀 Ejecutando script de despliegue en servidor..."
    ./despliegue/produccion/deploy_prod.sh
    
EOF

echo -e "\n${GREEN}✨ ¡Operación Completada! El servidor ha sido actualizado exitosamente.${NC}"
