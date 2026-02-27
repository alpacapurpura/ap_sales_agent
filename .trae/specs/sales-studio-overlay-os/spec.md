# Sales Studio "Overlay OS" Spec

## Why
Transformar el módulo de ventas actual en un "Centro de Comando Comercial" (Sales Studio) de alta eficiencia. El objetivo es centralizar la gestión de citas, pagos y conversaciones con leads en una interfaz unificada que priorice la velocidad, el contexto y la navegabilidad "1-click". Se busca eliminar la fricción de navegar entre múltiples páginas para tareas operativas diarias.

## What Changes
- **Refactorización Completa de `/sales/page.tsx`**:
  - Implementación de un diseño **Bento Grid** (Grilla modular) como vista principal.
  - Integración de paneles laterales (**Sheets**) y diálogos superpuestos (**Overlays**) para detalles y configuración, evitando recargas de página.
- **Nuevos Componentes de Interfaz**:
  - `SalesDashboard`: El contenedor principal con widgets de KPIs, Calendario Rápido y Actividad Reciente.
  - `SalesInboxSheet`: Un panel deslizante "siempre disponible" para gestionar conversaciones con leads sin salir del dashboard.
  - `PaymentGatewayConfig`: Componente de configuración "in-place" para pasarelas de pago (Culqi/MercadoPago), incluyendo toggle de **Modo Sandbox/Producción** y validación de API Keys.
  - `AppointmentSheet`: Vista detallada de citas con acciones rápidas (reprogramar, cancelar, marcar asistencia).
- **Lógica de Configuración Contextual**:
  - La configuración de disponibilidad y tipos de cita se realizará mediante un modal/sheet invocado directamente desde el widget de calendario.

## Impact
- **Affected Specs**: Módulo de Ventas, Gestión de Citas.
- **Affected Code**: 
  - `/frontend/src/app/(main)/(dashboard)/sales/page.tsx` (Reemplazo total).
  - Creación de nuevos componentes en `/frontend/src/features/sales/components/`.
  - Posible refactorización de `AvailabilityView` y `EventTypeView` para adaptarse a modales.

## ADDED Requirements
### Requirement: Sales Dashboard Bento Grid
El sistema DEBE presentar un dashboard modular (Bento Grid) que muestre de un vistazo:
- KPIs clave (Ventas, Tasa de Cierre, Citas).
- Calendario interactivo simplificado.
- Feed de actividad reciente (pagos, nuevos leads).
- Acceso rápido a herramientas (Inbox, Configuración).

#### Scenario: Visualización General
- **WHEN** el usuario entra a `/sales`
- **THEN** ve todos los módulos clave en una sola pantalla sin necesidad de scroll excesivo.

### Requirement: Contextual Navigation (Overlay OS)
El sistema DEBE permitir la navegación a detalles y configuraciones sin abandonar la vista principal.
- **WHEN** el usuario hace clic en una cita o una venta
- **THEN** se abre un `Sheet` (panel lateral) con los detalles, manteniendo el dashboard visible de fondo.

### Requirement: Payment Gateway Sandbox Configuration
El sistema DEBE permitir configurar pasarelas de pago (Culqi, MercadoPago) con soporte explícito para entornos de prueba.
- **WHEN** el usuario accede a la configuración de pagos
- **THEN** puede ingresar `Public Key` y `Secret Key` diferenciadas para **Modo Sandbox** y **Modo Producción**, y alternar entre ellos con un toggle.
- **THEN** puede ejecutar una "Prueba de Conexión" para validar las credenciales.

### Requirement: Sales Inbox Overlay
El sistema DEBE proporcionar acceso rápido a las conversaciones del bot.
- **WHEN** el usuario activa el "Inbox"
- **THEN** se despliega un panel lateral o flotante con la lista de conversaciones activas, permitiendo responder o intervenir sin cambiar de página.

## MODIFIED Requirements
### Requirement: Appointment Management
La gestión de citas (ver, reprogramar, cancelar) se realizará ahora dentro de un contexto de `Sheet` en lugar de una navegación de pestañas compleja.
- **Migration**: Adaptar `AppointmentsView` para funcionar como un widget del dashboard y como vista detallada en el `Sheet`.
