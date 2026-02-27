# Plan de Implementación: Gestión de Usuarios y Autenticación Estricta

Voy a modificar el sistema para permitir la creación de usuarios vinculados a Tenants desde el Admin y restringir el acceso exclusivamente a usuarios pre-registrados.

## 1. Capa de Servicios (Backend)
### A. Servicio de Integración con Clerk
Crearé un nuevo módulo `src/services/clerk.py` para manejar la comunicación con la API de Clerk.
- **Función `create_clerk_user`**:
    - Recibe `email`, `password`, `name`.
    - Realiza un POST a `https://api.clerk.com/v1/users` usando `CLERK_SECRET_KEY`.
    - Maneja errores (ej: "Usuario ya existe" - en cuyo caso procederemos a vincularlo en local).

### B. Refactorización de Autenticación (`dependencies.py`)
Modificaré `get_current_user` para aplicar la política de **Lista Blanca Estricta**:
- **Eliminar Auto-Creación**: Si el email del token no existe en la BD local -> `403 Forbidden` (Mensaje: "Acceso no autorizado. Contacte a su administrador").
- **Validación de Tenant**: Si el usuario existe pero `tenant_id` es nulo -> `403 Forbidden` (Mensaje: "Usuario sin organización asignada").
- **Sincronización**: Si el usuario existe, actualizar opcionalmente su `clerk_id` o `full_name` para mantener consistencia.

## 2. Capa de Administración (Admin Dashboard)
Modificaré `src/admin/app.py` para integrar la gestión de usuarios dentro de la sección de Tenants.

### Nueva Funcionalidad en `render_tenant_manager`:
- Al seleccionar un Tenant existente para editar, añadiré una sección **"👥 Gestión de Usuarios"**.
- **Tabla de Usuarios**: Listar usuarios actuales vinculados a ese Tenant.
- **Formulario "Nuevo Usuario"**:
    - Campos: Nombre Completo, Email, Contraseña.
    - **Acción**:
        1. Invocar `clerk_service.create_clerk_user` para crear la identidad en Clerk.
        2. Crear el registro en la tabla `User` de la base de datos local, asignando explícitamente el `tenant_id` del cliente seleccionado.

## 3. Flujo de Verificación
1. **Admin**: Crear un Tenant "Demo Corp".
2. **Admin**: Crear usuario "empleado@democorp.com" con contraseña.
3. **Login**: El usuario entra a la app cliente. Clerk autentica.
4. **Backend**: Verifica que "empleado@democorp.com" existe en BD y pertenece a "Demo Corp".
5. **Resultado**: El usuario accede y ve solo datos de "Demo Corp".
