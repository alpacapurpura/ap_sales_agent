Voy a realizar una serie de correcciones críticas en el backend para solucionar los errores de importación circular en SQLAlchemy y garantizar que la autenticación funcione correctamente tanto en desarrollo como en producción.

### **Diagnóstico del Problema**

1.  **Error de Inicialización de Modelos (Circular Imports):**
    Los logs de Python revelan que SQLAlchemy está fallando al inicializar las relaciones entre modelos (`Tenant`, `Lead`, `ChannelConnection`). Esto ocurre porque los modelos se importan entre sí de manera desordenada, causando que cuando `Tenant` intenta crear una relación con `ChannelConnection` o `Lead`, estas clases aún no están completamente definidas en el registro de SQLAlchemy.
    *   *Error específico:* `InvalidRequestError: ... expression 'ChannelConnection' failed to locate a name...`

2.  **Autenticación y Contexto (Causa Raíz del 403/401):**
    Aunque corregimos la dependencia en el router, el error de base de datos impide que la aplicación arranque correctamente o que las consultas de usuario/tenant funcionen, lo que lleva a fallos en cascada en `get_tenant_context`.

### **Plan de Solución**

1.  **Corregir Modelos SQLAlchemy (`backend/src/services/db/models/`):**
    *   Refactorizaré las importaciones en `tenant.py`, `business.py`, `lead.py`, `observability.py` y `channel_connection.py`.
    *   Usaremos **strings** para definir todas las relaciones (ej. `relationship("Lead", ...)` en lugar de importar la clase `Lead`), lo cual es la práctica recomendada por SQLAlchemy para evitar ciclos de importación.
    *   Centralizaré la importación de modelos en `backend/src/services/database.py` o un archivo `__init__.py` limpio para asegurar que todos se registren antes de crear las tablas.

2.  **Verificación de Dependencias (`backend/src/api/dependencies.py`):**
    *   Revisaré que `get_tenant_context` sea robusto ante fallos de base de datos y loguee claramente si el `user.tenant_id` es nulo o inválido.

3.  **Prueba de Integridad:**
    *   Ejecutaré un script de Python dentro del contenedor (similar al que falló) para verificar que ahora sí puedo consultar `User` y navegar a su `Tenant` sin errores de `InvalidRequestError`.

4.  **Validación Final:**
    *   Una vez corregido el modelo de datos, la API debería levantar sin errores y el endpoint `/health` y `/knowledge/stats` deberían responder 200 OK.

### **Por qué esto soluciona el problema de raíz:**
El error "Error al conectar con la API" en el frontend es un síntoma. La enfermedad real es que el ORM del backend está roto internamente por las referencias circulares. Al arreglar el modelo de datos, restauramos la capacidad del backend para autenticar usuarios y servir datos, independientemente de si estás en `localhost`, `salesagent.local` o `laptopchris...`.