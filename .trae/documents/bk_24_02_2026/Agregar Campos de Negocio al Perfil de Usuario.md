Voy a integrar los nuevos campos de negocio y asegurar su persistencia.

### Respuesta a tu pregunta
> ¿En qué parte del código se asegura la permanencia en base de datos del Agentstate?

La persistencia está garantizada en **`src/api/routes.py`**, en la línea 110:
```python
repo.persist_agent_state(user.id, result, active_product.id)
```
Esta función se ejecuta inmediatamente después de que el agente termina de procesar (`agent_app.ainvoke`), tomando el estado final (`result`) y guardándolo en la base de datos (PostgreSQL). Específicamente, llama a `repo.update_user_profile` para guardar el JSON del perfil.

### Plan de Acción Actualizado

1.  **Actualizar Esquema (`src/core/schema.py`)**:
    - Agregar `business_name`, `business_industry`, `business_details` a la clase `UserProfile`.
    - Esto permitirá que Pydantic valide y estructure estos datos cuando el agente los extraiga.

2.  **Validar Estado (`src/core/state.py`)**:
    - No se requieren cambios ya que `AgentState` usa `user_profile: Dict[str, Any]`, lo que automáticamente aceptará los nuevos campos del esquema actualizado.

3.  **Persistencia (Confirmada)**:
    - Como `routes.py` llama a `persist_agent_state` y este usa `user_profile.model_dump()` (indirectamente a través del dict del estado), los nuevos campos se guardarán automáticamente en la columna JSONB `profile_data` de la tabla `users`. No hace falta tocar `nodes.py` ni `routes.py` para esto, solo el esquema.

### Ejecución
Procederé a editar `src/core/schema.py` y luego reiniciaré el servicio para que los cambios surtan efecto.