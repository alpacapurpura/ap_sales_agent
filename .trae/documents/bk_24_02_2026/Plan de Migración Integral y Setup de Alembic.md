# Plan de Ejecución de Migración y Pipeline de Futuro (Alembic)

Este plan aborda dos objetivos críticos: **aplicar los cambios inmediatos** (Multitenancy) y **establecer un sistema profesional de migraciones** (Alembic) para el futuro, reemplazando el método actual de `create_all` que no soporta evoluciones de esquema.

## 1. Estrategia de Migración (Pipeline de Futuro)
Implementaremos **Alembic** como el estándar para cambios en la base de datos. Esto permitirá versionar el esquema SQL igual que el código Python.

### Pasos Técnicos:
1.  **Instalación**: Verificar/Instalar `alembic` y `psycopg2-binary`.
2.  **Inicialización**: Ejecutar `alembic init alembic` en `backend/`.
3.  **Configuración (`env.py`)**:
    *   Conectar Alembic con `Base.metadata` de tu aplicación para detectar modelos automáticamente.
    *   Configurar la URL de la DB usando tus `settings` (sin hardcodear credenciales).
4.  **Generación de Migración Inicial**:
    *   Crear una migración "Baseline" o "Multitenancy" que detecte:
        *   Nueva tabla `tenants`.
        *   Nuevas columnas `tenant_id` en todas las tablas existentes.

## 2. Ejecución de Cambios (Ahora)
Una vez configurado Alembic, ejecutaremos la migración para aplicar los cambios físicos en PostgreSQL.

### Script de Migración de Datos (`migrate_multitenancy.py`)
Dado que agregaremos columnas `NOT NULL` (o que deberían serlo lógicamente) a tablas con datos existentes, necesitamos un script intermedio que:
1.  **Ejecute la migración de esquema** (crear columnas como `NULL` inicialmente).
2.  **Cree el Tenant "System/Visionarias"**.
3.  **Backfill de Datos**: Asigne ese Tenant ID a todos los registros huérfanos existentes.
4.  **(Opcional)** Aplique restricciones `NOT NULL` si se desea estrictez futura.

### Script de Prompts
Ejecutar el script `migrate_prompts.py` que ya creamos para mover los `.j2` a la base de datos.

---

## 📅 Plan Detallado Paso a Paso

### Paso 1: Configurar Infraestructura Alembic
*   Crear `backend/alembic.ini`.
*   Crear carpeta `backend/alembic/` y configurar `env.py`.
*   **Pipeline Futuro**: De ahora en adelante, para cambiar la DB, solo ejecutarás:
    ```bash
    alembic revision --autogenerate -m "mensaje"
    alembic upgrade head
    ```

### Paso 2: Generar y Aplicar Migración de Esquema
*   Generar la revisión automática que detectará el `Tenant` model y los campos `tenant_id`.
*   Revisar el script generado para asegurar que maneja los `ForeignKey` correctamente.
*   Aplicar `alembic upgrade head`.

### Paso 3: Migración de Datos (Backfill)
*   Crear y ejecutar script `backend/scripts/init_tenant_data.py`:
    1.  Crea el Tenant "Visionarias".
    2.  Actualiza `users`, `products`, `messages`, etc., asignándoles este Tenant ID.

### Paso 4: Migración de Prompts
*   Ejecutar `python backend/scripts/migrate_prompts.py`.

### Paso 5: Verificación
*   Verificar que el sistema arranca y que los datos tienen `tenant_id`.
