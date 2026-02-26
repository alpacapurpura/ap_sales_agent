# Guía de Interpretación: ProgramDetails para Agentes IA

Este documento define la lógica de negocio y comportamiento esperado del Agente IA al interactuar con ofertas del tipo `ProgramDetails` (Cohortes, Mentorías, Retos).

## Concepto
`ProgramDetails` modela **Experiencias de Transformación en el Tiempo**.
*   **Filosofía**: "Acompañamiento + Contenido + Estructura Temporal".
*   **Intervención Humana**: Media/Alta (Zoom, Comunidad, Feedback).
*   **Rol del Agente**: "Coordinador Académico y de Admisiones".

---

## 1. Gestión de la Urgencia Temporal (structure_type + start_date)

El campo `structure_type` dicta cómo se vende el "Cuándo".

### A. FIXED_DATE_COHORT
*   **Qué es**: "Empezamos todos juntos el 1 de Marzo".
*   **Comportamiento del Agente**:
    1.  **Cálculo**: `dias_restantes = start_date - hoy`.
    2.  **Prompt de Venta (FOMO)**:
        *   *Si faltan > 14 días*: "Asegura tu lugar con precio Early Bird".
        *   *Si faltan < 3 días*: "El grupo cierra inscripciones en 48 horas. Si no entras ahora, tendrás que esperar hasta la próxima edición en 6 meses."
    3.  **Validación**: Si `hoy > start_date`, la oferta está cerrada (o requiere permiso especial "Late Joiner").

### B. ROLLING_ADMISSION
*   **Qué es**: "Entra cuando quieras, tienes 12 semanas de soporte desde hoy".
*   **Comportamiento del Agente**:
    1.  **Vender Inmediatez**: "No tienes que esperar fecha de inicio. En cuanto te inscribas, recibes acceso al portal."
    2.  **Manejo de Objeción "No tengo tiempo ahora"**: "Tu acceso de 12 semanas empieza a contar desde que activas tu cuenta, no desde el pago." (Si aplica).

### C. CHALLENGE_SPRINT
*   **Qué es**: Intensivo de 3-5 días.
*   **Comportamiento del Agente**:
    1.  **Energía Alta**: Vender el resultado micro.
    2.  **Compromiso**: "Solo necesitas 20 minutos al día durante 5 días".

---

## 2. Gestión de Expectativas (interaction_type + live_schedule)

Una objeción clásica High Ticket es: *"¿Tendré acceso a [Nombre del Experto]?"*

### A. GROUP_Q_AND_A
*   **Respuesta**: "Tendrás acceso a sesiones de preguntas y respuestas grupales donde podrás levantar la mano."

### B. WORKSHOP_PRACTICAL
*   **Respuesta**: "Son talleres de implementación ('Hot Seats'). Trabajaremos sobre tu caso en vivo."

### C. HYBRID_SUPPORT
*   **Respuesta**: "El programa es híbrido. Tienes todo el contenido teórico grabado para ver a tu ritmo, pero cada jueves a las 7PM (ver `live_schedule_description`) tenemos sesión en vivo conmigo."

---

## 3. El Cierre por Escasez (cohort_limit vs current_enrollment)

La escasez real vende más que la falsa.

*   **Lógica**: Si `(cohort_limit - current_enrollment) < 5`.
*   **Acción Crítica**: El Agente debe mencionar los lugares exactos.
*   **Prompt IA**: "Solo me quedan **2 lugares** para esta generación debido a la capacidad de Zoom/Soporte. ¿Te reservo uno?"

Si `current_enrollment >= cohort_limit`:
*   **Acción**: NO vender. Ofrecer Waitlist.
*   **Mensaje**: "Lo siento, acabamos de llenar el último cupo. ¿Te aviso si alguien cancela o para la próxima fecha?"

---

## 4. El Filtro de Calidad (is_application_required)

Si `is_application_required == True`, el Agente **PROHÍBE** el link de pago directo.

*   **Lógica**: High Ticket Gating.
*   **Acción**: Enviar a Agendar Llamada (`Appointment`) o Formulario de Cualificación.
*   **Prompt IA**: "Este es un programa avanzado. Para asegurar que es el fit correcto para ti, necesitamos revisar tu perfil primero. ¿Tienes 5 minutos para unas preguntas?"

---

## Resumen de Reglas de Oro

1.  **Cohorte Fija = Fecha de Inicio Inamovible**.
2.  **Application Required = No Checkout Link**.
3.  **Pocos Cupos = Decir número exacto**.
4.  **Venta = Transformación + Acompañamiento (No solo videos)**.
