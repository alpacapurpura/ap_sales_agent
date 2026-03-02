---
module: Sales Agent
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Manejar conversaciones multi-canal (WhatsApp/Telegram/Manychat), aplicar tácticas de ventas, manejar objeciones y cerrar ventas o agendar citas de forma autónoma con los leads entrantes.

## 2. Reglas de Negocio Estrictas (Business Rules)
- Las conversaciones se gestionan mediante grafos de estado (State Machines - LangGraph).
- La memoria es episódica y se resume para no saturar el contexto (buffer_service.py).
- Puntos de Salida (Exit Points): Si el bot detecta insultos, spam, o no sabe responder (safety_check), debe derivar a un humano de inmediato.

## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/sales_agent/ (Agents, Orchestrator, LLM Providers).
- Frontend: frontend/src/features/sales/ y frontend/src/features/audit/ (Para ver las trazas y logs del Agente).

## 4. Casos Borde Conocidos (Edge Cases)
- Concurrency (Condiciones de Carrera): Un usuario manda 5 mensajes rápidos seguidos por WhatsApp. El sales_agent dispara 5 ejecuciones paralelas del LLM si no hay un sistema de cola/debounce.
- Alucinación de Enlaces: El modelo genera URLs de pago falsas en lugar de pedirlas de forma estructurada.