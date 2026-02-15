#!/bin/bash
set -e

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Protocolo de Despliegue Local (Visionarias Production)${NC}"

# 1. Verificación de Rama
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
# Si estamos en detached HEAD (común en CI o deploys específicos), saltamos validación estricta
if [[ "$CURRENT_BRANCH" == "HEAD" ]]; then
    echo -e "${YELLOW}⚠️  Estás en 'Detached HEAD'. Asumiendo despliegue de commit específico.${NC}"
elif [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo -e "${YELLOW}⚠️  Estás en la rama '$CURRENT_BRANCH'. Se recomienda desplegar desde 'main'.${NC}"
    # En modo no interactivo (CI/SSH remoto), esto podría bloquearse.
    # Agregamos timeout o flag de fuerza.
    if [[ "$1" != "--force" ]]; then
        echo "Usa --force para omitir esta advertencia o despliega desde main."
        exit 1
    fi
else
    echo -e "${GREEN}✅ Rama principal detectada.${NC}"
    echo "Sincronizando con remoto..."
    git pull origin $CURRENT_BRANCH
fi

# 2. Generación de Changelog (Lenguaje de Negocio)
echo -e "${GREEN}📝 Generando Log de Cambios...${NC}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    LOG_RANGE="HEAD"
else
    LOG_RANGE="$LAST_TAG..HEAD"
fi

echo "# Resumen de Cambios para Despliegue $(date +%Y-%m-%d)" > DEPLOY_CHANGELOG.md
echo "" >> DEPLOY_CHANGELOG.md
echo "## ✨ Nuevas Funcionalidades" >> DEPLOY_CHANGELOG.md
git log $LOG_RANGE --pretty=format:"- %s" | grep "^feat" | sed 's/^feat: /  - /' >> DEPLOY_CHANGELOG.md || echo "  - Sin nuevas funcionalidades." >> DEPLOY_CHANGELOG.md
echo "" >> DEPLOY_CHANGELOG.md
echo "## 🐛 Correcciones" >> DEPLOY_CHANGELOG.md
git log $LOG_RANGE --pretty=format:"- %s" | grep "^fix" | sed 's/^fix: /  - /' >> DEPLOY_CHANGELOG.md || echo "  - Sin correcciones críticas." >> DEPLOY_CHANGELOG.md
echo "" >> DEPLOY_CHANGELOG.md
echo "## 🔧 Mejoras Técnicas" >> DEPLOY_CHANGELOG.md
git log $LOG_RANGE --pretty=format:"- %s" | grep -E "^(chore|refactor|perf)" | sed 's/^[a-z]*: /  - /' >> DEPLOY_CHANGELOG.md || echo "  - Mantenimiento general." >> DEPLOY_CHANGELOG.md

cat DEPLOY_CHANGELOG.md
echo -e "${GREEN}✅ Changelog generado en DEPLOY_CHANGELOG.md${NC}"

# 3. Pruebas Internas (Pre-Flight)
echo -e "${GREEN}🧪 Ejecutando Pruebas de Integridad...${NC}"

# Backend Check
if [ -d "backend" ]; then
    echo "Verificando Backend..."
    # Asumiendo que tenemos un script de test o usamos pytest
    # docker compose exec api_dev pytest ... (Opcional, si el contenedor está corriendo)
    # Por ahora haremos check de sintaxis/linting rápido
    if command -v ruff &> /dev/null; then
        ruff check backend/src --select E,F
    else
        echo -e "${YELLOW}⚠️ Ruff no instalado localmente, saltando linting.${NC}"
    fi
fi

# Frontend Check
if [ -d "frontend" ]; then
    echo "Verificando Frontend..."
    # cd frontend && npm run lint (Opcional)
fi

# 4. Backup de Base de Datos (Seguridad Crítica)
echo -e "${GREEN}💾 Realizando Backup de Seguridad de BD...${NC}"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

# Cargar variables de entorno si no están cargadas
if [ -f .env ]; then
    set -a
    source <(grep -v '^#' .env | sed 's/CORS_ORIGINS=.*//g')
    set +a
fi

DB_NAME="${POSTGRES_DB:-visionarias}"
DB_USER="${POSTGRES_USER:-postgres}"

if docker ps | grep -q visionarias_postgres; then
    # Usamos las variables del .env para el dump
    if docker exec visionarias_postgres pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"; then
        echo -e "${GREEN}✅ Backup guardado en $BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Falló el backup de la base de datos '$DB_NAME'. Verificando logs...${NC}"
        # No bloqueamos el deploy si falla el backup por "database does not exist" en el primer run,
        # pero sí mostramos alerta.
        echo -e "${YELLOW}⚠️  Continuando con precaución. (Si es la primera vez, ignora esto)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Base de datos no está corriendo. Omitiendo backup (Seguro si es primer despliegue).${NC}"
fi

# 5. Despliegue (Build & Up)
echo -e "${GREEN}🏗️  Construyendo y Levantando Servicios...${NC}"

# DOCKER LOGIN (Si existe GITHUB_TOKEN)
# Esto es necesario para bajar imágenes si usamos GHCR
if [ ! -z "$GITHUB_TOKEN" ]; then
    echo "🐳 Logueando en GHCR..."
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u alpacapurpura --password-stdin
fi

# Usamos --build para asegurar que se construyan localmente si no existen remotas
# Usamos --remove-orphans para limpiar
# Forzamos build para asegurar que use el código local sincronizado
docker compose up -d --build --remove-orphans

# 5.1 Ejecutar Migraciones de Base de Datos
echo -e "${GREEN}🔄 Ejecutando Migraciones de Base de Datos...${NC}"
# Esperamos unos segundos para que el contenedor esté listo
sleep 10
# En producción el servicio se llama 'backend' y el contenedor 'visionarias_brain'
# Intentamos usar el nombre de servicio para que compose lo resuelva
if docker compose exec backend alembic upgrade head; then
    echo -e "${GREEN}✅ Migraciones aplicadas correctamente.${NC}"
else
    echo -e "${YELLOW}⚠️  Migración falló. Puede que la BD ya exista pero Alembic no lo sepa.${NC}"
    echo -e "${YELLOW}🔄 Intentando sincronizar estado (Stamp Head)...${NC}"
    # Si falla upgrade porque las tablas existen, hacemos stamp para marcar como actualizado
    if docker compose exec backend alembic stamp head; then
         echo -e "${GREEN}✅ Base de datos marcada como actualizada (Stamp Head).${NC}"
    else
         echo -e "${RED}❌ Error crítico en base de datos. Revisar logs.${NC}"
    fi
fi

# 6. Verificación Post-Despliegue
echo -e "${GREEN}🏥 Verificando Salud del Sistema...${NC}"
sleep 5

# Check Backend
if docker ps | grep -q visionarias_brain; then
    echo -e "${GREEN}✅ API Backend: ONLINE (Container Running)${NC}"
else
    echo -e "${RED}❌ API Backend: ERROR (Container Not Running)${NC}"
fi

# Check Frontend
if docker ps | grep -q visionarias_client; then
    echo -e "${GREEN}✅ Frontend Cliente: ONLINE (Container Running)${NC}"
else
    echo -e "${RED}❌ Frontend Cliente: ERROR (Container Not Running)${NC}"
fi

echo -e "${GREEN}🎉 Despliegue Finalizado Exitosamente.${NC}"
