Voy a actualizar el esquema de datos (`UserProfile`) y la plantilla de prompts para soportar la extracción de los nuevos campos solicitados.

### Cambios Planificados:

1.  **Actualizar `src/core/schema.py`**:
    *   Agregar los siguientes campos a la clase `UserProfile`:
        *   `age`: Edad del usuario (Optional[str]).
        *   `email`: Correo electrónico (Optional[str]).
        *   `phone`: Teléfono (Optional[str]).
        *   `gender`: Género (Literal["Masculino", "Femenino", "No binario"]).
        *   `relation`: Relación con el cliente real (Literal["friend", "partner", "wife", "coworker", "daughter"]).
        *   `user_type`: Tipo de usuario (Literal["himself", "Other"]). Usaré un alias para que coincida con la salida "user" del prompt.
        *   `user_name`: Nombre de la persona que averigua (si es para otro).

2.  **Refinar `src/core/prompts/templates/state_transition.j2`**:
    *   Asegurar que las instrucciones de extracción coincidan exactamente con los nuevos campos.
    *   Aclarar la distinción entre `name` (cliente potencial) y `user_name` (persona que averigua), para evitar confusiones en la IA.

3.  **Verificar `src/core/nodes.py`**:
    *   La lógica actual ya actualiza dinámicamente el perfil usando `extracted_info`. Al actualizar el esquema Pydantic, los nuevos campos serán aceptados automáticamente y dejarán de ser ignorados.

Esto permitirá que el Agente recuerde estos datos clave y los visualice en el panel de auditoría.