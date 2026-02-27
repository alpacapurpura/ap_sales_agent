# Implementación de Indicador "Escribiendo..." Post-Debounce

He comprendido tu solicitud. Quieres que, una vez que el bot ha decidido "es mi turno de hablar" (después de toda la espera del debounce), **refuerce** el indicador visual de "Escribiendo..." para que el usuario sepa que su respuesta está siendo procesada, aprovechando la API `sendChatAction`.

Esto es crucial porque el primer indicador "Escribiendo..." (línea 170) ocurre *durante* la espera. Si la espera es larga (como acabamos de configurar a 4s/6s), ese primer indicador podría expirar o simplemente el usuario necesita la confirmación visual de "OK, ya terminó de esperar, ahora está pensando la respuesta".

## 🛠️ Plan de Implementación

1. **Ajustar Tiempos de Debounce (Lo solicitado previamente):**

   * Aumentaré los tiempos de espera a **2.0s** (frase completa) y **4.0s** (incompleta) en `smart_debounce_task`.

2. **Inyectar** **`set_typing_status`** **Post-Debounce:**

   * Ubicación: Justo antes de llamar a `_execute_agent_flow` (Línea 223 aprox) o dentro de `_execute_agent_flow` al inicio.

   * Decisión Arquitectónica: Lo pondré al inicio de `_execute_agent_flow`. ¿Por qué? Porque esa función es la que encapsula "el trabajo del agente". Así, cada vez que el agente empieza a trabajar (Persistencia, RAG, LLM), garantizamos que el usuario vea "Escribiendo...".

### Código a Modificar (`src/api/routes.py`)

**1. Ajuste de Tiempos:**

```python
if is_complete:
    wait_time = 4.0  # Antes 0.5
else:
    wait_time = 6.0  # Antes 1.5
```

**2. Refuerzo de Typing:**

```python
async def _execute_agent_flow(channel_adapter, incoming: IncomingMessage):
    # 0. Reforzar indicador de "Escribiendo..." ahora que empezamos a procesar de verdad
    await channel_adapter.set_typing_status(incoming.user_id)
    
    # ... resto del código ...
```

Esto cubrirá exactamente el flujo que describes:

1. Espera (con typing intermitente).
2. Decisión de responder.
3. **Typing explícito (5s)** mientras el LLM piensa.
4. Respuesta enviada.

