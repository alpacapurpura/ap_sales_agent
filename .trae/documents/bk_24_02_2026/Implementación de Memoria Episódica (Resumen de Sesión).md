# Implementación Técnica Detallada: Memoria Episódica

Entiendo perfectamente tu solicitud. No quieres generalidades, sino la "cirugía" exacta en el código para que el sistema recuerde contextos pasados sin convertirse en un monstruo inmanejable.

Aquí está el plan de implementación detallado para la **Memoria Episódica (Session Summary)**:

## 1. El Concepto Técnico
Vamos a aprovechar que ya tenemos un modelo de datos `User` con un campo JSONB `psychographics`. En lugar de crear tablas nuevas, añadiremos una clave `last_session_summary` dentro de este JSON.

**Flujo de Datos:**
1.  **Detección de Cierre:** No podemos saber cuándo la usuaria "cierra" WhatsApp. Por lo tanto, generaremos el resumen de forma **asíncrona/oportunista** cada vez que el `node_state_manager` detecte un cambio de estado importante o después de X mensajes.
2.  **Generación:** Un LLM ligero (GPT-4o-mini o similar) leerá los últimos 10 mensajes y actualizará el resumen.
3.  **Inyección:** Al iniciar una nueva charla (`node_entry_point`), si existe un resumen previo y han pasado >6 horas, lo inyectamos en el prompt del sistema como "Contexto Previo".

---

## 2. Cambios Específicos en Archivos

### A. `src/core/nodes.py` - Modificar `node_state_manager`
Añadiremos lógica para detectar hitos y actualizar el resumen.

```python
# Pseudo-código de la implementación
def node_state_manager(state: AgentState):
    # ... lógica existente ...
    
    # NUEVO: Generación de Memoria Episódica
    # Solo generamos resumen si hubo un cambio de estado significativo
    # o si la conversación ha avanzado (para no gastar tokens en cada mensaje)
    if next_state != state["current_state"] or len(state["messages"]) % 5 == 0:
        
        # Lanzamos tarea de resumen (idealmente async, pero aquí síncrono por simplicidad inicial)
        summary = generate_session_summary(state["messages"], state["user_profile"])
        
        # Guardamos en el perfil persistente
        state["user_profile"]["last_session_summary"] = summary
        # Actualizamos en Redis/DB
        repo.update_user_profile(user_id, {"last_session_summary": summary})
```

### B. `src/core/prompts/templates/summary_generator.j2` (Nuevo Archivo)
Crearemos un prompt especializado para condensar la charla.

```jinja2
Analiza esta conversación de ventas y genera un resumen de 2 líneas.
Enfócate en:
1. Qué dolor/problema confesó la usuaria.
2. En qué objeción o duda se quedó.
3. Nivel de interés (Bajo/Medio/Alto).

Output Ejemplo: "María tiene un negocio de velas estancado. Le preocupa el precio y debe consultar con su esposo. Interés Alto."
```

### C. `src/core/prompts/templates/sales_system.j2` (Modificación)
Inyectaremos este resumen en el prompt principal para que el agente lo use.

```jinja2
# ...
CONTEXTO DEL USUARIO:
Ocupación: {{ user_profile.occupation }}
...
{% if user_profile.last_session_summary %}
MEMORIA DE SESIÓN ANTERIOR:
{{ user_profile.last_session_summary }}
(Usa esto para saludar o retomar el hilo si han pasado horas, pero no seas repetitiva).
{% endif %}
# ...
```

---

## 3. ¿Por qué esta implementación?
*   **No rompe nada:** Es puramente aditiva sobre la estructura JSON existente.
*   **Eficiente:** Solo resume en hitos clave, no en cada mensaje.
*   **Humana:** Permite que el bot diga "Hola de nuevo, ¿pudiste pensar lo que hablamos sobre tu negocio de velas?" en lugar de un "Hola" genérico.

¿Procedemos a escribir estos cambios específicos?