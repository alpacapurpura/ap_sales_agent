# Plan de Migración a Arquitectura API-First

Este plan detalla los pasos para transformar la aplicación actual en una arquitectura escalable de 3 pilares (Backend API, Admin Panel, Client Dashboard), siguiendo estrictamente la recomendación del usuario.

## 1. Backend Refactor ("API-ficación")

El objetivo es exponer la lógica de negocio (actualmente consumida directamente por Streamlit) a través de endpoints REST en FastAPI.

### 1.1 Crear Routers en `src/api/routers/`

Crearemos módulos organizados para agrupar los endpoints:

* **`src/api/routers/knowledge.py`**:

  * `GET /stats`: Wrapper de `kb_service.get_system_stats()`

  * `POST /ingest`: Wrapper de `kb_service.ingest_file()` (Manejo de UploadFile)

  * `GET /documents`: Wrapper de `kb_service.list_documents()`

  * `DELETE /documents/{filename}`: Wrapper de `kb_service.delete_document()`

  * `POST /search`: Wrapper de `kb_service.search()`

  * `PATCH /documents/{filename}/category`: Wrapper de `kb_service.update_document_category()`

* **`src/api/routers/admin.py`**:

  * `POST /sync`: Wrapper de `kb_service.sync_from_qdrant()`

  * `GET /audit/users`: Wrapper de `repo.get_recent_users()`

### 1.2 Actualizar `src/main.py`

* Importar e incluir los nuevos routers (`knowledge_router`, `admin_router`) en la aplicación FastAPI principal.

* Asegurar que CORS esté configurado para permitir peticiones desde el nuevo frontend (localhost:3000).

## 2. Docker Architecture Update

Separaremos los entornos de ejecución en `docker-compose.yml` para garantizar desacoplamiento real.

### 2.1 Definir Servicios

* **`api`** **(Backend)**:

  * Usa el Dockerfile Python actual.

  * Comando: `uvicorn src.main:app --host 0.0.0.0 --port 8000`

  * Puerto: `8000:8000`

* **`admin_dashboard`** **(Streamlit)**:

  * Reusa la imagen de `api` (mismo contexto).

  * Comando: `streamlit run src/admin/app.py`

  * Puerto: `8501:8501`

  * Acceso directo a DB permitido (como "Super Usuario").

* **`client_dashboard`** **(Frontend)**:

  * Nuevo servicio basado en Node.js.

  * Contexto: `./frontend`

  * Puerto: `3000:3000`

  * Variable de entorno: `NEXT_PUBLIC_API_URL=http://localhost:8000` (Cliente) o `http://api:8000` (Server-side).

## 3. Frontend Setup (Next.js)

Inicializaremos la estructura básica del cliente para cumplir con el "Paso 2".

### 3.1 Estructura de Archivos

* Crear directorio `frontend/`.

* **`frontend/Dockerfile`**: Imagen ligera de Node.js (Alpine).

* **`frontend/package.json`**: Configuración manual con dependencias de Next.js 14, React, Tailwind y Lucide (iconos).

* **`frontend/next.config.js`**: Configuración básica.

* **`frontend/app/page.tsx`**: Landing page simple ("Client Dashboard") que probará la conexión con la API.

## 4. Ejecución y Verificación

1. Aplicar cambios de código en Backend.
2. Crear archivos del Frontend.
3. Actualizar `docker-compose.yml`.
4. Ejecutar `docker compose up --build`.
5. Verificar acceso a:

   * API Docs: `http://localhost:8000/docs`

   * Admin Panel: `http://localhost:8501`

   * Client Dashboard: `http://localhost:3000`

