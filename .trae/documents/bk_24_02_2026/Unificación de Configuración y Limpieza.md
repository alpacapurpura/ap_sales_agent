# Unificación de Configuración `.env` y Solución de Errores

El usuario ha planteado dos puntos importantes:
1.  **Dualidad de archivos `.env`**: Existe uno en la raíz y otro en `backend/.env` (que es un symlink en sistemas Linux/Mac, pero en Windows/WSL a veces se comporta como copia desactualizada). Esto causa confusión y desincronización.
2.  **Errores de Ejecución**: El backend falló por falta de librerías, y esto cascada al frontend.

## Plan de Acción

### 1. Unificar `.env` (Fuente Única de Verdad)
Para evitar discrepancias, eliminaré el `.env` de `backend/` y configuraré `docker-compose.yml` para que use explícitamente el `.env` de la raíz (`../.env` desde el contexto de build, o `./.env` desde el contexto de compose).
- **Acción**: Borrar `backend/.env`.
- **Acción**: Verificar que `docker-compose.yml` ya apunta a `.env` (lo cual hace en la línea 11: `- .env`). Al estar el compose en la raíz, ya lee el archivo correcto. El problema era la existencia del archivo duplicado que podría estar siendo leído por scripts locales o herramientas como Pylance/VSCode.

### 2. Verificar y Corregir Variables
El usuario tiene un túnel Cloudflare en `laptopchris.alpacapurpura.lat`.
- **Backend**: Necesita saber que su dominio público es ese, para generar webhooks y redirects correctos.
- **Frontend**: Necesita saber que la API está en ese dominio (o en localhost si es dev local).
- **Corrección**: Aseguraré que `GOOGLE_REDIRECT_URI` en el `.env` raíz sea correcto y que el backend lo lea.

### 3. Validación Final
- Reiniciar el stack para asegurar que todos los contenedores (especialmente `api_dev`) lean las variables limpias y tengan las librerías instaladas (ya reconstruido en el paso anterior, pero un reinicio limpio asegura lectura de env).

Procederé a eliminar la redundancia y confirmar la operación.