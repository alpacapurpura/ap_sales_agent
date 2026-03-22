# Visionarias Brain - AI Sales Agent

Sistema de agente de ventas basado en Inteligencia Artificial, diseñado con una arquitectura "Code-First" utilizando Python, FastAPI y LangGraph.

## Características

*   **Arquitectura Pura Python**: Eliminación de dependencias Low-Code (n8n) para mayor control y latencia reducida.
*   **LangGraph State Machine**: Control determinista del flujo de conversación (S1 -> S6).
*   **Dockerized**: Perfiles de despliegue para Desarrollo y Producción.
*   **RAG Híbrido**: Integración con Qdrant para recuperación de contexto.
*   **Telemetría**: Logging estructurado en PostgreSQL.

## Estructura del Proyecto

```
.
├── docker-compose.yml      # Orquestación de servicios
├── src/
│   ├── api/                # Endpoints (Webhook WhatsApp)
│   ├── core/               # Lógica del Agente (LangGraph)
│   ├── services/           # Integraciones (Redis, DB, WA)
│   └── main.py             # Entrypoint
```

## Configuración

1.  Copiar el archivo de ejemplo:
    ```bash
    cp .env.example .env
    ```
2.  Editar `.env` con tus credenciales de Meta (WhatsApp API) y OpenAI.

## Comandos Rápidos (Makefile)

Este proyecto incluye un `Makefile` para simplificar la gestión de Docker y permisos.

| Comando | Descripción |
| :--- | :--- |
| `make setup` | **Ejecutar primero.** Crea carpetas de datos/logs con permisos correctos. |
| `make dev` | Inicia el entorno de **Desarrollo** (Hot-reload, puertos expuestos). |
| `make prod` | Inicia el entorno de **Producción** (Optimizado, usa `.env.prod`). |
| `make stop` | Detiene todos los contenedores. |
| `make logs-prod` | Sigue logs del carril de producción (`docker-compose.prod.yml`). |
| `make shopify-config-dev` | Activa configuración Shopify de desarrollo (`shopify.app.dev.toml`). |
| `make shopify-config-prod` | Activa configuración Shopify de producción (`shopify.app.prod.toml`). |
| `make shopify-config-status` | Muestra nombre, URL y client_id de la configuración activa. |
| `make fix-permissions` | Repara problemas de propiedad (candados) en archivos generados por Docker. |
| `make install-front p=lib` | Instala librerías npm en Host y Docker simultáneamente. |

## Rutina segura Shopify (selección de carril)

### Flujo de desarrollo (dev)

```bash
make shopify-config-dev
make shopify-config-status
make dev
```

### Flujo de release/despliegue (prod)

```bash
make shopify-config-prod
make shopify-config-status
make prod
```

## Runbook diario de desarrollo Shopify (sin impactar distribución)

### Inicio de jornada

1. Activar explícitamente carril dev:
   ```bash
   make shopify-config-dev
   make shopify-config-status
   ```
2. Verificar que `shopify.app.toml` muestre app dev (`name` y `application_url` de desarrollo).
3. Levantar entorno:
   ```bash
   make dev
   ```

### Ciclo diario de trabajo

1. Implementar cambios con carril dev activo.
2. Validar OAuth embebido y flujo de conexión en dev store principal.
3. Si se tocan callbacks/scopes/webhooks, volver a ejecutar `make shopify-config-status` antes de pruebas finales.
4. Mantener la app de distribución fuera del ciclo diario: no ejecutar `make shopify-config-prod` durante desarrollo activo.

### Cierre de jornada

1. Dejar evidencia mínima en PR/issue: tienda validada, resultado OAuth, resultado compliance.
2. Confirmar que la configuración activa sigue en dev:
   ```bash
   make shopify-config-status
   ```

## Gate de release Shopify (dev -> prod)

### 1) Smoke tests en carril dev (obligatorio)

1. Activar carril dev:
   ```bash
   make shopify-config-dev
   make shopify-config-status
   ```
2. Verificar en dev store principal:
   - La app embebida abre sin loop de OAuth.
   - Instalación/reinstalación funciona.
   - Conexión OAuth completa deja canal activo.
   - Endpoints de compliance responden 2xx.

### 2) Validación secundaria en `visionarias.lat`

Con la misma configuración dev, ejecutar una pasada corta en `visionarias.lat`:
- Reautorizar o instalar app dev.
- Abrir app embebida y validar carga inicial.
- Ejecutar reconexión OAuth.
- Confirmar ausencia de 401/403/500 en logs backend durante handshake.

### 3) Criterios de salida para promover a prod

Solo promover cuando todo esté en verde:
- Smoke tests dev completados.
- Validación secundaria en `visionarias.lat` completada.
- Sin cambios pendientes de scopes/webhooks entre carriles.
- Configuración activa cambiada a prod antes de desplegar:
  ```bash
  make shopify-config-prod
  make shopify-config-status
  ```

### 4) Promoción operativa a App Store (dev -> prod)

1. Congelar cambios funcionales y cerrar QA del carril dev.
2. Activar carril prod y validar identidad de app:
   ```bash
   make shopify-config-prod
   make shopify-config-status
   ```
3. Aplicar configuración productiva al Partner Dashboard:
   ```bash
   cd shopify_app
   npx shopify app config push
   ```
4. Desplegar backend/frontend productivo y validar OAuth + compliance en carril prod.
5. Publicar actualización en App Store únicamente cuando los checks anteriores estén en verde.

### 5) Rollback operativo de configuración (incidente en release)

1. Detener promoción y bloquear nuevos cambios.
2. Reaplicar configuración productiva estable:
   ```bash
   make shopify-config-prod
   make shopify-config-status
   cd shopify_app
   npx shopify app config push
   ```
3. Revertir despliegue a build/commit estable previo según tu pipeline de release.
4. Validar recuperación mínima: carga embebida, OAuth callback, endpoints de compliance en 2xx.
5. Reabrir carril dev para corrección:
   ```bash
   make shopify-config-dev
   make shopify-config-status
   ```

## Despliegue

### Desarrollo (Development)

```bash
make setup
make dev
```

Acceso: `http://localhost:8000/docs`

### Producción (Production)

Diseñado para correr detrás de un Traefik existente.

1.  Asegúrate de que la red externa existe:
    ```bash
    docker network create web_gateway || true
    ```
2.  Lanzar servicios:
    ```bash
    make prod
    ```

El servicio estará disponible en `https://salesagent.alpacapurpura.lat`.
