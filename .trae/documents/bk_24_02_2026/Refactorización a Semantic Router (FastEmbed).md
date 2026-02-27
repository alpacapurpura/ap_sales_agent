# Plan de Arquitectura "Visionarias High-Ticket" (2026)

Tras analizar el documento `FUNNEL_ESTRATÉGICO...md`, la arquitectura óptima debe combinar la **calidez humana** del copy (Ileana) con la **precisión técnica** de un sistema de ventas.

El problema actual es que el `router` por palabras clave (`if "precio" in msg`) es demasiado torpe para un funnel tan emocional y ramificado. Por ejemplo, si una usuaria dice *"Me da miedo que sea muy caro para mí"*, el router actual podría mandarlo a "Objeción Crítica" (agresivo), cuando el documento sugiere una validación emocional primero ("El miedo no significa que no debas hacerlo").

## Nueva Arquitectura: "Semantic Intent Router" (Híbrido)

Implementaremos un **Router Semántico Local (FastEmbed)** que clasifique la intención de la usuaria en 3 niveles antes de decidir quién responde.

### Nivel 1: Ruteo de FAQs y Logística (Velocidad <50ms, Cero Costo)
Usaremos `fastembed` para comparar el mensaje con las **21 Preguntas Frecuentes** del documento.
*   **Ejemplo:** "¿Cuándo empieza?" -> Detecta intención `faq_start_date` -> Respuesta inmediata con "10 de Febrero 2026".
*   **Ejemplo:** "¿Cómo pago?" -> Detecta intención `faq_payment` -> Respuesta inmediata con las 4 opciones (Tarjeta, Yape, Transferencia).
*   **Beneficio:** Latencia nula para datos duros. Precisión 100% (sin alucinaciones).

### Nivel 2: Ruteo de "Estado Emocional" (El Corazón del Funnel)
El documento define estados claros (Rama 1, 2, 3). El router detectará en qué "Rama" está la usuaria según sus respuestas, mapeando lenguaje natural a los "Botones" del flujo.
*   **Usuario:** "Siento que hago todo yo sola y me agota" -> Router detecta: `pain_point: delegar` -> Estado: `Rama 1 / Pregunta 5`.
*   **Acción:** El `Manager` recibe este input limpio y avanza el estado del funnel.

### Nivel 3: Ruteo de Seguridad y Descalificación
*   **Regla de Oro (FAQ #9):** Si la usuaria dice "No tengo idea ni negocio", el router detecta `disqualification_no_business` y ejecuta el script de "salida suave" definido en el doc ("En un futuro...").

---

## Plan de Ejecución (Paso a Paso)

1.  **Servicio de Ruteo Semántico (`src/services/router_service.py`)**:
    *   Crear clase `SemanticRouter` usando `fastembed` y `qdrant-client` (ya instalados).
    *   Cargar "Intenciones Ancla" extraídas del documento (FAQs, Dolores, Objeciones).

2.  **Refactorizar `node_router` (`src/core/nodes.py`)**:
    *   Eliminar la lógica de `if "string"` frágil.
    *   Integrar `SemanticRouter.detect_intent(msg)`.
    *   **Lógica de Salida:**
        *   Si es FAQ -> `router_outcome: "direct_response"` (Generator usa template de respuesta rápida).
        *   Si es Objeción -> `router_outcome: "objection_handling"` (Generator usa script emocional).
        *   Si es Conversación -> `router_outcome: "sales_flow"` (Manager decide estrategia).

3.  **Actualizar `node_manager`**:
    *   Hacerlo consciente de las "Ramas" (1, 2, 3) del documento para que sepa qué preguntar después.

Esta arquitectura reduce tus llamadas a OpenAI (las FAQs y validaciones simples salen por router) y aumenta la conversión (detecta el dolor exacto para responder con el copy de Ileana).
