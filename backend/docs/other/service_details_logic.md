# Guía de Interpretación: ServiceDetails para Agentes IA

Este documento define la lógica de negocio y comportamiento esperado del Agente IA al interactuar con ofertas del tipo `ServiceDetails` (Mentorías 1:1, Agencias, Patrocinios).

## Concepto
`ServiceDetails` modela **Servicios Profesionales y B2B**.
*   **Categoría**: Heterogénea (Advisory, Agency, Authority).
*   **Recursos Críticos**: Tiempo, Capital Humano y Autoridad.
*   **Riesgo**: Alto (Scope Creep, Problemas Legales).

---

## 🧠 Diccionario de Datos para la IA (Interpretación de Negocio)

Cuando tu Agente "Setter" o "Account Manager" lea una oferta con `ServiceDetails`, debe ejecutar los siguientes Guiones Mentales (Scripts) según los datos encontrados:

### Escenario 1: El "VIP Day" (Advisory + One-Off + Sync)
*   **Datos Clave**: `category=ADVISORY`, `frequency=ONE_OFF`, `interaction=SYNC`, `booking_url=...`
*   **Rol IA**: Asistente Ejecutiva.
*   **Lógica**: "Pago recibido. El recurso más escaso aquí es el tiempo."
*   **Acción Inmediata**: Enviar el link de agenda (`booking_url`) y preparar al cliente para una sesión intensiva.
*   **Script**: "Tu siguiente paso INMEDIATO es bloquear tu día en este link: [booking_url]. Tienes [session_duration_minutes] minutos intensivos, así que ven preparada."

### Escenario 2: El "Pack de Edición de Video" (Agency + Retainer + Async)
*   **Datos Clave**: `category=AGENCY`, `frequency=RETAINER`, `interaction=ASYNC`, `brief_url=...`, `turnaround=3`
*   **Rol IA**: Project Manager.
*   **Lógica**: Gestionar inputs y SLAs.
*   **Acción Inmediata**: Solicitar Brief y Crudos (`onboarding_brief_url`).
*   **Script**: "Bienvenida al servicio mensual. Para que tu primer video esté listo en [turnaround_time_days] días, necesito que subas tus crudos y llenes este brief: [onboarding_brief_url]. Recuerda que tienes [revision_rounds] rondas de cambios incluidas por video."

### Escenario 3: La "Mención en Podcast" (B2B + One-Off + Authority)
*   **Datos Clave**: `category=AUTHORITY`, `audience=15k Listeners`, `usage_rights=Organic Only`
*   **Rol IA**: Media Sales Representative.
*   **Lógica**: Vender alcance y proteger la marca legalmente.
*   **Acción Inmediata**: Solicitar activos de la marca (`technical_requirements`) y firmar contrato si aplica.
*   **Script**: "Gracias por confiar en Visionarias para tu campaña. Llegaremos a [audience_reach_metric]. OJO: Este paquete permite uso [usage_rights_description]. Por favor envíanos tu [technical_requirements] antes del viernes para entrar en la pauta."

---

## Campos Clave Agregados y Su Propósito

1.  **`revision_rounds`**: Vital para agencias creativas. Evita el infierno de cambios infinitos ("Solo un cambio más...").
2.  **`onboarding_brief_url`**: Diferencia clave entre "Agendar una llamada" (Consultoría) y "Llenar un form" (Agencia).
3.  **`audience_reach_metric`**: El activo principal de un influencer B2B. Justifica el precio del patrocinio.
4.  **`requires_contract_signature`**: Gatillo para procesos legales externos. La venta no termina con el pago.
5.  **`deliverables_list`**: Convierte una promesa vaga en una lista de chequeo contractual. Protege contra disputas.

---

## Validaciones de Negocio (Guardrails)

La IA está programada para **rechazar** configuraciones peligrosas:
*   ❌ Vender TIEMPO (Sync) sin AGENDA (`booking_url`).
*   ❌ Vender TRABAJO (Agency) sin LISTA DE ENTREGABLES (`deliverables_list`).
*   ❌ Vender PATROCINIO (Authority) sin REQUISITOS TÉCNICOS (`technical_requirements`).
