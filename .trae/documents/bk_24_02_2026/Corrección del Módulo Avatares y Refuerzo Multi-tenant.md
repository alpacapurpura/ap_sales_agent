# Diagnóstico y Solución: Error en Avatares y Modelo Multi-tenant

Tras revisar el código, he confirmado que la política de usuario actual se respeta (no se crean usuarios automáticamente aquí), pero existe un **bug crítico** en la implementación del módulo de Avatares que causa el error y, potencialmente, una brecha de seguridad en el modelo multi-tenant.

## Diagnóstico Detallado

1.  **Causa del Error ("Error al cargar los avatares"):**
    *   El frontend recibe un error **500 Internal Server Error** del backend.
    *   **El motivo:** El archivo de rutas (`routers/avatars.py`) intenta enviar el `tenant_id` al repositorio para filtrar los datos (lo cual es correcto para la seguridad):
        `repo.list_avatars(scope=scope, tenant_id=user.tenant_id)`
    *   Sin embargo, la función `list_avatars` en el repositorio (`repositories/avatar.py`) **no acepta este argumento**:
        `def list_avatars(self, scope: str = "GLOBAL") -> List[AvatarDefinition]:`
    *   Esto provoca que Python lance un `TypeError: unexpected keyword argument 'tenant_id'`, rompiendo la petición.

2.  **Fallo en el Modelo Multi-tenant (Aislamiento):**
    *   Actualmente, las funciones del repositorio (`list_avatars`, `get_by_id`, etc.) **ignoran por completo el tenant**.
    *   Si se corrigiera solo el error del argumento sin añadir el filtro, un usuario de "Visionarias" podría ver (o editar/borrar) los avatares de *cualquier otro cliente*, rompiendo el aislamiento de datos.

## Plan de Solución

Para solucionar el error y garantizar que "lo que hagas sea solo para este cliente", implementaré los siguientes cambios en `backend/src/services/db/repositories/avatar.py`:

1.  **Corregir `list_avatars`:**
    *   Añadir el parámetro `tenant_id`.
    *   Agregar el filtro `.filter(AvatarDefinition.tenant_id == tenant_id)` a la consulta SQL.

2.  **Blindar el resto de operaciones (`get`, `update`, `delete`, `set_default`):**
    *   Todas estas funciones también están fallando o son inseguras porque no validan que el objeto pertenezca al tenant del usuario.
    *   Modificaré cada función para requerir `tenant_id` y asegurar que nadie pueda manipular datos de otro cliente, incluso si adivinan un ID.

Esto resolverá el mensaje de error en el frontend y asegurará el estricto cumplimiento de la política multi-tenant que solicitas.