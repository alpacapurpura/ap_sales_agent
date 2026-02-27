Entendido. Para cumplir con tu requerimiento de **tablas separadas** y evitar problemas futuros de integridad o mezcla de conceptos, implementaré la siguiente arquitectura.

### Estrategia: "Migración por Renombrado" (Segura para Datos)

Dado que la tabla `users` actual contiene miles de interacciones (mensajes, enrollments) asociadas a leads, lo más seguro es **transformar la tabla `users` actual en la tabla `leads`** y crear una tabla `users` nueva y limpia para el sistema.

#### 1. Refactorización de Modelos (Backend)
*   **Nuevo Modelo `Lead` (`leads`)**:
    *   Heredará la estructura actual de `User` (Telegram ID, Profile Data, Enrollments).
    *   Representará exclusivamente a los usuarios del chatbot.
    *   Ubicación: `src/services/db/models/lead.py`
*   **Nuevo Modelo `User` (`users`)**:
    *   Estructura limpia: `id`, `email`, `full_name`, `tenant_id`, `role`.
    *   Representará exclusivamente a los administradores y staff con acceso al dashboard.
    *   Ubicación: `src/services/db/models/user.py`

#### 2. Actualización de Relaciones (Foreign Keys)
Actualizaré los modelos dependientes (`Message`, `Enrollment`, `Appointment`) para que apunten a la tabla correcta:
*   Los mensajes y citas pertenecerán a `Lead` (`leads.id`).
*   Mantendremos la columna física `user_id` en la tabla `messages` (para evitar migraciones pesadas) pero la mapearemos lógicamente como `lead_id` en el código Python.

#### 3. Script de Migración Automática
Crearé y ejecutaré un script (`scripts/migrate_split_users.py`) que realizará:
1.  **Renombrado de Tabla**: `ALTER TABLE users RENAME TO leads;` (Conserva todo el historial de chats).
2.  **Creación de Tabla**: `CREATE TABLE users ...` (Nueva tabla para accesos).
3.  **Duplicación Selectiva**: Copiará a los usuarios que tienen email (como tú, el developer) desde `leads` hacia la nueva tabla `users`.
    *   *Resultado:* Existirás en `users` (para hacer login) Y en `leads` (para tus pruebas de chat), que es el comportamiento correcto.

#### 4. Actualización del Dashboard (`app.py`)
*   **Tenant Manager**: Leerá de la nueva tabla `User`. Solo verás personal administrativo.
*   **Auditoría**: Leerá de la tabla `Lead`. Solo verás gente que ha chateado.

Esta solución es robusta, separa los conceptos físicamente y preserva el 100% de la data histórica de tus pruebas.