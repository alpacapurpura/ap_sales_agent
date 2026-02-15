#!/bin/bash
set -e

# ==========================================
# DESPLIEGUE REMOTO (Trigger desde Laptop)
# ==========================================
# Este script se conecta al servidor de producción y ejecuta el protocolo de despliegue seguro.
# Combina la comodidad local con la seguridad del script de servidor.

# Cargar variables de entorno locales si existen (para overrides)
if [ -f .env.prod ]; then
    # Exportamos las variables para que estén disponibles, ignorando líneas comentadas y corrigiendo sintaxis de arrays
    # 1. Leemos el archivo
    # 2. Ignoramos comentarios
    # 3. Reemplazamos arrays JSON como CORS_ORIGINS por strings simples para evitar errores de bash
    # 4. Exportamos
    set -a
    source <(grep -v '^#' .env.prod | sed 's/CORS_ORIGINS=.*//g')
    set +a
fi

# Configuración del Servidor (Valores por defecto o desde .env.prod)
SERVER_IP="${SERVER_IP:-161.132.41.191}"
SERVER_USER="${SERVER_USER:-root}"
SERVER_PORT="${SERVER_PORT:-22022}"
SSH_KEY_PATH="${SSH_KEY_PATH:-/home/chris/.ssh/id_rsa}"
REMOTE_PATH="${REMOTE_PATH:-/opt/ap_sales_agent}" # Ruta real en producción

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Iniciando Secuencia de Despliegue a Producción${NC}"
echo "Target: $SERVER_USER@$SERVER_IP:$REMOTE_PATH"

# 1. Verificar Estado Local
echo -e "\n${YELLOW}1. Verificando estado local...${NC}"
if [[ -n $(git status -s) ]]; then
    echo "❌ Tienes cambios sin commitear. Por favor haz commit y push antes de desplegar."
    echo "   Esto asegura que lo que hay en producción coincida con el repositorio."
    exit 1
fi

echo "Sincronizando rama main local..."
git checkout main
git pull origin main
echo "Subiendo cambios a GitHub..."
git push origin main

# 2. Conexión SSH y Ejecución Remota
echo -e "\n${YELLOW}2. Conectando al servidor para ejecutar despliegue...${NC}"

# Subir archivos de configuración críticos antes de ejecutar el script remoto
echo "📤 Subiendo configuraciones locales (Homologación)..."
scp -i $SSH_KEY_PATH -P $SERVER_PORT docker-compose.prod.yml $SERVER_USER@$SERVER_IP:$REMOTE_PATH/docker-compose.yml
scp -i $SSH_KEY_PATH -P $SERVER_PORT .env.prod $SERVER_USER@$SERVER_IP:$REMOTE_PATH/.env

# FORCE MANUAL UPLOAD OF DEPLOY SCRIPT
# Como git fetch está fallando, subimos el script manualmente
echo "📤 Creando estructura de directorios remota..."
ssh -i $SSH_KEY_PATH -p $SERVER_PORT $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_PATH/despliegue/local"

echo "📤 Subiendo script de despliegue manualmente..."
scp -i $SSH_KEY_PATH -P $SERVER_PORT despliegue/local/deploy.sh $SERVER_USER@$SERVER_IP:$REMOTE_PATH/despliegue/local/deploy.sh

echo "   Se ejecutará: ./despliegue/local/deploy.sh en el servidor."

# Usamos el token proporcionado para autenticar
GITHUB_TOKEN="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"

ssh -i $SSH_KEY_PATH -p $SERVER_PORT $SERVER_USER@$SERVER_IP << EOF
    set -e
    
    echo "📍 Conectado a \$(hostname)"
    
    # Asegurar que existe el directorio
    if [ ! -d "$REMOTE_PATH" ]; then
        echo "❌ No encuentro el directorio del proyecto en $REMOTE_PATH"
        exit 1
    fi
    
    cd $REMOTE_PATH
    
    # SKIP GIT FETCH AUTOMATIC
    # Debido a problemas con git en modo no-interactivo, confiamos en el script subido manualmente
    # y ejecutamos directamente.
    
    # Asegurar permisos de ejecución
    chmod +x despliegue/local/deploy.sh
    
    # Exportar token para que deploy.sh lo use
    export GITHUB_TOKEN="$GITHUB_TOKEN"
    
    # Ejecutar el script maestro de despliegue
    # Pasamos --force si se requiere, o argumentos adicionales
    ./despliegue/local/deploy.sh
    
EOF

echo -e "\n${GREEN}✨ ¡Operación Completada! El servidor ha sido actualizado.${NC}"
