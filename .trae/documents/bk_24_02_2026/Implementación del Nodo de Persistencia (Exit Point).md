# Diseño del Nodo `node_exit_point` (Capa de Persistencia)

Como arquitecto de software, entiendo que buscas desacoplar la lógica de persistencia del flujo principal del agente y de la capa de API (`routes.py`). Esto es una excelente práctica ("Separation of Concerns") que mejora la mantenibilidad y testabilidad.

Actualmente, la persistencia ocurre de forma dispersa en `src/api/routes.py` (después de `ainvoke`) y parcialmente en el nodo `manager` (memoria episódica). Vamos a centralizar esto en un nodo final dedicado.

## 🏗️ Propuesta Arquitectónica

El nuevo nodo `node_exit_point` será el **responsable final** antes de que el ciclo del grafo termine. Su contrato es simple: **"Lo que entra aquí, se guarda para siempre"**.

### Responsabilidades del Nodo:
1.  **Persistencia del Estado del Funnel (`Enrollment`):** Guardar en qué etapa quedó el usuario (`stage`, `status`, `lead_score`).
2.  **Persistencia del Perfil (`UserProfile`):** Guardar cualquier dato nuevo descubierto sobre el usuario (nombre, email, dolores).
3.  **Gestión de Sesión:** Asegurar que el `AgentState` quede listo para la próxima interacción (limpieza de flags temporales).
4.  **No Modifica la Respuesta:** Este nodo **NO** debe alterar el mensaje que va al usuario (`messages`), solo "observa y guarda".

## 🛠️ Plan de Implementación

1.  **Crear `node_exit_point` en `src/core/nodes.py`:**
    *   Este nodo recibirá el estado final (ya procesado por `safety_layer`).
    *   Extraerá `user_profile` y llamará a `UserRepository.update_profile`.
    *   Extraerá `current_state` y `lead_score` y llamará a `BusinessRepository.persist_agent_state`.
    *   Manejará excepciones de forma silenciosa para no bloquear la respuesta al usuario (logging de errores críticos).

2.  **Actualizar el Grafo en `src/core/agent.py`:**
    *   Insertar `node_exit_point` al final de la cadena.
    *   Flujo: `... -> safety_layer -> exit_point -> END`.

3.  **Limpieza en `src/api/routes.py`:**
    *   Eliminar la lógica de persistencia duplicada que existe actualmente después de `agent_app.ainvoke`. La API solo debe encargarse de enviar el mensaje, no de guardar el estado del negocio.

### Diagrama del Nuevo Flujo
```
[Entry] -> [Router] 
              |-> [Direct Response] -> [Exit Point] -> END
              |-> [Manager] -> [Generator] -> [Safety Layer] -> [Exit Point] -> END
```

Esta estructura garantiza que **pase lo que pase** (respuesta directa o generada), siempre pasamos por el punto de control de persistencia.
