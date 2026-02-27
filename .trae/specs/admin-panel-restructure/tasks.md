# Tasks

- [x] Task 1: Backend Service Enhancements (Clerk)
  - [x] SubTask 1.1: Agregar método `update_user_password` a `ClerkService` en `backend/src/services/clerk.py`.
  - [x] SubTask 1.2: Agregar método `ban_user` (y `unban_user`) a `ClerkService`.
  - [x] SubTask 1.3: Agregar método `delete_user` a `ClerkService` (opcional, para limpieza en errores de creación).

- [x] Task 2: Streamlit Structure & Tenant Management
  - [x] SubTask 2.1: Limpiar `backend/src/admin/app.py` y crear estructura de navegación (Sidebar: Tenants, Users).
  - [x] SubTask 2.2: Implementar vista "Tenants": Tabla con columnas ID, Slug, Platform Keys (Checkbox).
  - [x] SubTask 2.3: Implementar formulario "Crear Tenant": Inputs para Name, Slug, y Checkbox `can_use_platform_keys`. Guardar en DB.

- [x] Task 3: User Management Implementation
  - [x] SubTask 3.1: Implementar vista "Usuarios": Dropdown para seleccionar Tenant -> Tabla de usuarios filtrada.
  - [x] SubTask 3.2: Implementar formulario "Crear Usuario": Inputs (Email, Password, Name). Lógica de transacción dual (Clerk -> DB). Manejo de errores (si falla DB, borrar de Clerk).
  - [x] SubTask 3.3: Implementar acciones en tabla: Botón "Cambiar Password" (Modal/Input) y Botón "Bloquear/Desbloquear".

- [x] Task 4: Verification & Cleanup
  - [x] SubTask 4.1: Verificar flujo completo: Crear Tenant -> Crear Usuario -> Loguearse con ese usuario (simulado o real).
  - [x] SubTask 4.2: Eliminar código muerto de módulos anteriores en `backend/src/admin/`.
