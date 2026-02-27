# Plan Definitivo: Máquina de Estados High-Ticket & Captura de Datos

Este plan implementa tu "Cognitive Architecture" respetando el Funnel Visionarias y asegurando la captura de datos críticos (Nombre, Estado del Negocio) desde el inicio.

## 1. El Cerebro: `node_state_manager` (Cognitive Architecture)

Transformaremos el nodo `node_state_manager` para ejecutar tus 3 fases en cada turno, con énfasis especial en S1 y S2 para la captura de datos.

### **Fase A: Análisis de Estado (State Analysis)**
El nodo verificará estrictamente las condiciones de cada etapa:

*   **S1 (Rapport) - "La Puerta de Entrada"**:
    *   **Objetivo**: Saludo + **Capturar Nombre** + **Capturar Estado del Emprendimiento**.
    *   **Lógica**: Si no tenemos `full_name` o `business_stage` en el perfil, el agente *debe* preguntarlos antes de avanzar. No se pasa a S2 sin esto.
*   **S2 (Discovery) - "El Filtro"**:
    *   **Objetivo**: Llenar las variables del Funnel (Rubro, Tiempo, Equipo, Facturación, Dolor).
    *   **Lógica**: Loop de preguntas hasta completar `revenue_tier` y `pain_point`.
*   **S3 (Gap)**: Agitar el costo de inacción usando el `pain_point` detectado.
*   **S4 (Pitch)**: Presentar la solución como puente.
*   **S5 (Anchoring)**: Revelar precio (S/. 5,000 / Oferta S/. 4,444) solo tras interés.
*   **S6 (Closing)**: **Objetivo: Agendar Micro-llamada (15min)**.

### **Fase B: Selección de Estrategia (Strategy Selection)**
Lógica condicional según perfil:
*   *Emprendedora consolidada (>10k)* → **ROI Reframing**.
*   *Inicios/Empleada* → **Career Capital**.
*   *Miedo detectado* → **Risk Reversal** (Garantía 7 días).

### **Fase C: Reglas de Transición (Transition Policy)**
| De | A | Trigger Estricto |
| :--- | :--- | :--- |
| **S1** | **S2** | Tenemos `full_name` + `business_stage` + Permiso implícito. |
| **S2** | **S3** | Tenemos `revenue_tier` + `pain_point`. (Si falta, se queda en S2). |
| **S3** | **S4** | Usuario admite urgencia ("Necesito cambiar esto"). |
| **S4** | **S5** | Usuario pregunta "¿Cómo funciona?" o "¿Precio?". |
| **S5** | **S6** | Usuario acepta precio o pide facilidades. |
| **S*** | **Downsell** | "No tengo negocio" o "No puedo pagarlo" (Hard No). |

---

## 2. Implementación Técnica

### A. Prompt `state_transition.j2` (Nuevo)
Crearemos este prompt para que el LLM actúe como "Juez de Transición".
*   *Input*: Historial, Estado Actual, Perfil Actual.
*   *Output JSON*:
    ```json
    {
      "next_state": "S1_Rapport",
      "missing_info": ["full_name", "business_stage"],
      "strategy": "none"
    }
    ```

### B. Persistencia de Datos (ORM)
*   Aseguraremos que cuando el agente extraiga `full_name` y `business_stage` en S1/S2, se guarden en `state["user_profile"]`.
*   Tu `repository.py` ya está configurado para guardar este diccionario en la columna `psychographics` del modelo `User`, garantizando que no se pierdan datos entre sesiones.

### C. Manejo de Objeciones (Script Registry)
*   Cargaré las respuestas del FAQ (doc Visionarias) en el sistema.
*   Si el usuario pregunta por "Garantía" o "Tiempo", el Router semántico inyectará la respuesta oficial del documento sin romper el flujo del estado.

¿Procedo a implementar el `node_state_manager` con esta lógica estricta de captura de datos y transición?