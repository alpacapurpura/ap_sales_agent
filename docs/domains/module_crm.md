---
module: CRM
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
- Convertir interacciones temporales en relaciones duraderas. Gestiona a los usuarios que ya compraron, administra su historial (LTV), y orquesta campañas de retención (Upselling, Cross-selling, NPS).

## 2. Reglas de Negocio Estrictas (Business Rules)
- Resolución de Identidad (Golden Record): Un usuario no entra al CRM hasta que su identidad esté validada por una transacción o acción clave. El CRM unifica múltiples interacciones (Ej: El mismo usuario desde 2 teléfonos distintos).
- Consistencia de Eventos: Su actualización suele ser reactiva escuchando eventos (Ej: "VentaCerrada") emitidos por el sales_agent o pasarelas de pago.
- Notificaciones y Campañas: Decide y redacta campañas de email marketing masivas, newsletters o tácticas de retención (upsell). Para el envío físico masivo o transaccional, DEBE invocar a src/shared/mailing/.

## 3. Mapa de Código
- Backend: backend/src/modules/crm/
- Frontend: en construcción

## 4. Casos Borde Conocidos (Edge Cases)
- Falsos Positivos de Identidad: Dos familiares usando el mismo email o número de contacto unificando por error dos perfiles distintos en un solo Customer.
- Escalabilidad de Histórico: Consultas lentas (N+1) al renderizar el historial de vida de un cliente con cientos de interacciones pasadas y transacciones pequeñas.