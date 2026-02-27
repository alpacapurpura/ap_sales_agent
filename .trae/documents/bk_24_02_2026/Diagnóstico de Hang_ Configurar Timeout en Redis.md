Entendido, tienes toda la razón. Usar Redis para duplicar el historial es ineficiente y consume RAM innecesariamente cuando **PostgreSQL ya tiene toda la verdad**.

### 🏗️ Nuevo Plan de Arquitectura: "Postgres Only"

Voy a refactorizar el sistema para eliminar la dependencia de Redis en el flujo crítico del chat, resolviendo tanto el problema de memoria como el "bloqueo" (hang) actual.

#### 1. Backend (`src/services/repository.py`)
*   Implementaré un método eficiente `get_chat_history(user_id, limit=10)` que traiga los últimos mensajes directamente de la base de datos, formateados como lista de diccionarios (`[{"role": "user", "content": "..."}, ...]`).

#### 2. API (`src/api/routes.py`)
*   En lugar de pasar solo el mensaje actual al agente, inyectaré el historial completo recuperado de la DB en el `initial_state`.
*   Esto elimina la necesidad de que el agente "cargue" memoria externa.

#### 3. Core (`src/core/nodes.py`)
*   **Limpieza Total:** Eliminaré todas las llamadas a `redis_client` (lectura y escritura).
*   **Node Entry:** Ya no buscará en Redis. Simplemente validará que el estado venga correcto desde la API.
*   **Persistencia:** Dado que `routes.py` ya guarda el input del usuario y el output del asistente en Postgres, no necesitamos guardar nada manualmente dentro de los nodos.

### 🚀 Beneficios
1.  **Memoria RAM:** Liberamos espacio al no cachear chats en Redis.
2.  **Estabilidad:** Eliminamos el punto de fallo (Hang) actual con Redis.
3.  **Consistencia:** Una sola fuente de verdad (Postgres).

Procederé con estos cambios ahora mismo.