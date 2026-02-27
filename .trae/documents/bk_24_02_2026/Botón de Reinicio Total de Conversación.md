Entendido. Para permitir reiniciar una conversación "desde cero" de manera efectiva, no basta con borrar los mensajes visuales; también debemos borrar la "memoria" del agente (Trazas) y reiniciar su estado en el embudo de ventas.

### 🛠️ Plan de Implementación

1.  **Backend (`src/services/repository.py`):**
    *   Crearé un método `clear_user_conversation(user_id)` que realizará una limpieza profunda:
        *   🗑️ **Borrar Mensajes:** Elimina todo el historial de chat (`Message`).
        *   🧠 **Borrar Trazas:** Elimina los logs de pensamiento (`AgentTrace`) y llamadas LLM (`LLMCallLog`) asociados.
        *   🔄 **Reiniciar Embudo:** Restablece cualquier `Enrollment` activo a la etapa inicial (`S1_Rapport`, status `awareness`) y limpia el puntaje (`lead_score`).
        *   👤 **Limpiar Perfil (Opcional):** Reinicia los datos psicográficos (`pain_points`, `desires`) para que el agente vuelva a hacer las preguntas de descubrimiento.

2.  **Frontend (`src/admin/app.py`):**
    *   En la pestaña de **Auditoría**, agregaré un botón rojo **"🗑️ Limpiar Conversación"** en la barra lateral o panel principal cuando un usuario esté seleccionado.
    *   Al confirmar, ejecutará la limpieza y recargará la página.

### 🧪 Resultado Esperado
Al pulsar el botón, el usuario quedará como si fuera "nuevo" en el sistema, permitiéndote probar el flujo de bienvenida y cualificación desde el principio sin "residuos" de sesiones anteriores.