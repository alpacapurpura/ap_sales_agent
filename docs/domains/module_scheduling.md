---
module: Scheduling
status: active
core_files: []
---

## 1. Propósito del Negocio (El "Por Qué")
Ser el motor de gestión de tiempos y disponibilidad de los dueños del negocio / empleados y gestiona la reservas de citas (Appointments).

## 2. Reglas de Negocio Estrictas (Business Rules)
- Agnóstico de Ventas: Solo sabe de bloques de tiempo y reservas, no sabe si es para una venta, soporte o reclamo.
- Zonas Horarias Estrictas: Toda la disponibilidad se ingresa en el Timezone del usuario, pero se convierte forzosamente a UTC absoluto para almacenarse en la base de datos.
- Notificaciones: Decide y redacta correos de confirmación, reprogramación o recordatorio de citas. Para el envío físico, DEBE invocar a src/shared/mailing/ sin implementar lógica de envío directa.
## 3. Mapa de Código (Rutas relativas a Front y Back para este módulo)
- Backend: backend/src/modules/scheduling/
- Frontend: Rutas dinámicas públicas frontend/src/app/(main)/book/ y vistas de gestión interna.

## 4. Casos Borde Conocidos (Edge Cases)
- Colisión Horaria (Double Booking): Dos usuarios de WhatsApp intentando agendar el último slot disponible del viernes a las 3:00 PM con milisegundos de diferencia.
- Zonas Horarias Fronterizas: Problemas de conversión en días donde aplica el cambio de horario de verano (DST) generando reuniones adelantadas o atrasadas una hora.