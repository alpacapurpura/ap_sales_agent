Voy a actualizar la página de reservas (`frontend/src/app/book/[tenant_slug]/[event_slug]/page.tsx`) para implementar los límites de fechas y la visualización de disponibilidad.

### 1. Respetar Plazos (Límites de Tiempo)
**Problema**: El calendario permite navegar indefinidamente.
**Solución**:
*   Calcularé la fecha máxima permitida usando `max_advance_days` (60 días por defecto) desde la fecha actual.
*   Configuraré las propiedades `fromDate` (hoy) y `toDate` (hoy + 60 días) en el componente `Calendar`. Esto deshabilitará visualmente y bloqueará la navegación a fechas fuera del rango permitido.

### 2. Visualización de Disponibilidad (Días Claros)
**Problema**: No se sabe qué días tienen horarios hasta que se hace clic.
**Solución**:
*   Implementaré una carga automática de "Disponibilidad Mensual": Cada vez que cambies de mes en el calendario, la aplicación consultará todos los horarios de ese mes en segundo plano.
*   Procesaré esos datos para identificar qué días tienen al menos un horario libre.
*   Usaré los **Modificadores de Estilo** del Calendario para aplicar un fondo más claro (`bg-neutral-800` o similar) a los días con disponibilidad, diferenciándolos de los días sin horarios o bloqueados.

### Pasos de Implementación
1.  **Estado**: Agregar variables para rastrear la disponibilidad del mes actual (`availableDays`).
2.  **Efecto**: Crear un `useEffect` que detecte cambios en `month` y consulte la API (`publicApi.getEventTypeSlots`) para el rango `startOfMonth` a `endOfMonth`.
3.  **Renderizado**: Actualizar el componente `<Calendar />` con:
    *   `disabled`: Fechas pasadas o futuras fuera del límite.
    *   `modifiers`: Marcar días disponibles.
    *   `modifiersClassNames`: Estilos CSS para resaltar esos días (estilo Cal.com).
