# Optimización con Multi-stage Builds

Voy a refactorizar tu `Dockerfile` utilizando el patrón **Multi-stage Build** para reducir drásticamente el tamaño de la imagen final y mejorar la seguridad.

## Estructura Propuesta

### Etapa 1: Builder (`builder`)

Esta etapa se encargará del "trabajo sucio" y pesado:

* Instalar compiladores (`gcc`, `build-essential`) necesarios para librerías como `psycopg2` o `numpy` (usado por `langchain`/`pandas`).

* Crear un entorno virtual (`/opt/venv`).

* Instalar todas las dependencias de Python aquí.

* **Beneficio**: Todo el peso de las herramientas de compilación y cachés se queda aquí y no pasa a producción.

### Etapa 2: Runtime (`final`)

Esta etapa será la imagen que realmente correrá:

* **Base Limpia**: `python:3.11-slim` (sin compiladores).

* **Usuario No-Root**: Crearemos un usuario `appuser` para que la aplicación no corra como `root` (Práctica de Seguridad Crítica).

* **Solo lo necesario**:

  * Instalamos solo librerías de sistema *runtime* (`libpq5` para Postgres).

  * Copiamos el entorno virtual (`/opt/venv`) desde la etapa `builder`.

  * Copiamos el código fuente.

* **Configuración**: Variables de entorno y `PATH` ajustado para usar el venv automáticamente.

## Cambios en Archivos

1. **`Dockerfile`**: Reescritura completa.
2. **`docker-compose.yml`**: No requiere cambios (ya usa `build: .`), pero reconstruiremos los contenedores para aplicar la optimización.
3. **`.dockerignore`** (Opcional pero recomendado): Verificaré si existe para asegurar que no copiamos basura (como `__pycache__` o `.git`) al contexto de build.

## Beneficios Esperados

* 📉 **Menor Tamaño**: Eliminamos cientos de MB de herramientas de compilación.

* 🛡️ **Mayor Seguridad**: Ejecución sin privilegios de root y menor superficie de ataque.

* 🚀 **Eficiencia**: Mejor uso del caché de Docker layers.

