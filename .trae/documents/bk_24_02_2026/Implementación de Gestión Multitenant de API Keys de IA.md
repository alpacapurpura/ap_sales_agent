# Plan de Implementación de API Keys Personalizadas (Multitenant)

Este plan detalla los cambios necesarios en Backend y Frontend para permitir que los usuarios configuren sus propias API Keys de OpenAI y Gemini, cumpliendo con la lógica de permisos multitenant solicitada.

## Backend (FastAPI + SQLAlchemy)

### 1. Actualización del Modelo de Datos
Modificaremos la tabla `users` para almacenar las credenciales y el permiso.
*   **Archivo:** `src/services/db/models/user.py`
*   **Cambios:**
    *   Agregar columna `openai_api_key` (String, nullable).
    *   Agregar columna `gemini_api_key` (String, nullable).
    *   Agregar columna `can_use_platform_keys` (Boolean, default=False).
*   **Migración:** Se generará un script SQL/Python para aplicar estos cambios manualmente en la base de datos (dado que no hay migraciones automáticas).

### 2. Lógica de Negocio y Patrón Factory
Adaptaremos el patrón Factory existente para inyectar dinámicamente la API Key correcta según el usuario.
*   **Archivos:**
    *   `src/core/llm/base.py`: Actualizar interfaz si es necesario (generalmente el `__init__`).
    *   `src/core/llm/providers/openai.py` y `gemini.py`: Modificar constructores para aceptar `api_key` opcional.
    *   `src/core/llm/factory.py`:
        *   Modificar `get_service` (o crear `get_service_for_user`) para recibir el contexto del usuario.
        *   **Lógica de Selección:**
            1.  Si el usuario tiene Key propia -> Usar Key del usuario.
            2.  Si no tiene Key propia y `can_use_platform_keys=True` -> Usar Key del .env.
            3.  Si no tiene Key propia y `can_use_platform_keys=False` -> Lanzar `MissingAPIKeyError`.

### 3. Endpoints de Configuración
Crear endpoints para que el usuario guarde sus llaves y el admin gestione permisos.
*   **Archivo:** `src/api/routers/user.py` (o nuevo `settings.py`)
    *   `PATCH /users/me/api-keys`: Para que el usuario actualice sus keys.
    *   `PATCH /admin/users/{id}/permissions`: Para que el superadmin active/desactive `can_use_platform_keys`.

## Frontend (Next.js + Shadcn UI)

### 1. Nueva Página de Configuración (Usuario)
Crearemos la sección donde el usuario gestiona sus llaves.
*   **Archivo:** `src/app/(dashboard)/settings/page.tsx` (Nueva página).
*   **Diseño:**
    *   Layout con Tabs verticales (usando componentes Shadcn).
    *   Tab **"AI API Key's"**:
        *   Formulario con campos para OpenAI y Gemini (ocultos por defecto con `type="password"`).
        *   **Lógica UX:**
            *   Si `!user_keys` Y `!can_use_platform_keys`: Mostrar alerta roja/amarilla indicando "Configuración Requerida: No tienes permiso para usar las llaves de la plataforma".
            *   Si `can_use_platform_keys`: Mostrar mensaje "Puedes usar tus propias llaves o dejarlo vacío para usar las del sistema".

### 2. Dashboard Superadmin
Actualizar la lista de usuarios para gestionar permisos.
*   **Archivo:** `src/components/audit/user-list.tsx` (o donde se listen los clientes).
*   **Cambios:**
    *   Agregar columna o acción "Permisos AI".
    *   Implementar un `Switch` (Toggle) para `can_use_platform_keys`.

## Verificación
1.  **Escenario 1 (Sin Permiso, Sin Llaves):** Intentar usar el bot -> Debe fallar con mensaje claro. Ver alerta en Dashboard.
2.  **Escenario 2 (Con Permiso, Sin Llaves):** Intentar usar el bot -> Debe funcionar usando credenciales del `.env`.
3.  **Escenario 3 (Con Llaves Propias):** Intentar usar el bot -> Debe funcionar usando las credenciales del usuario (verificable via logs o uso de cuota).
