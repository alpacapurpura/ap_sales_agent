# Estructura Detallada para la Nueva Sección "Conexiones"

A continuación, presento la propuesta técnica para implementar la sección "Conexiones" siguiendo el patrón de diseño de Manychat y la arquitectura actual del proyecto (Next.js + Shadcn UI).

## 1. Integración en el Menú Principal
Se añadirá la nueva opción en la barra lateral global (`app-sidebar.tsx`), respetando la jerarquía solicitada.

*   **Ubicación:** Entre "Auditoría" y "Configuración".
*   **Ruta:** `/connections`
*   **Icono:** `Link` (de Lucide React) para representar integraciones/conexiones.
*   **Archivo:** `frontend/src/components/layout/app-sidebar.tsx`

## 2. Estructura de la Página (`/connections`)
La página seguirá el mismo patrón de diseño que "Configuración" (`/settings`), utilizando un layout de dos columnas con pestañas verticales, pero añadiendo la **agrupación por categorías** que solicitaste.

### Layout Visual
*   **Contenedor Principal:** `flex flex-col lg:flex-row`
*   **Panel Izquierdo (Navegación Secundaria):** Un sidebar vertical (`aside`) que contiene los grupos y pestañas. Ocupará aprox. el 20% del ancho (`lg:w-1/5`).
*   **Panel Derecho (Contenido):** Área dinámica que cambia según la pestaña seleccionada.

### Organización del Menú Secundario
El menú se construirá utilizando el componente `Tabs` de Shadcn UI, con una estructura personalizada para los grupos:

#### Grupo 1: Canales de Venta
*   *Título:* Texto pequeño, gris y en negrita (`text-muted-foreground`, `font-semibold`).
*   *Items:*
    *   WhatsApp (Icono: `MessageCircle`)
    *   TikTok (Icono: `Video` o `Music2`)
    *   Instagram (Icono: `Instagram`)
    *   Messenger (Icono: `MessageSquare`)
    *   Telegram (Icono: `Send`)
    *   Web Widget (Icono: `MessageSquareCode`)

#### Grupo 2: Herramientas
*   *Items:*
    *   Calendario (Icono: `Calendar`)
    *   CRM (Icono: `Users`)
    *   Pasarela de Pagos (Icono: `CreditCard`)

#### Grupo 3: Desarrolladores
*   *Items:*
    *   Webhooks (Icono: `Webhook`)

## 3. Comportamiento y Estado
*   **Persistencia de URL:** Al igual que en "Configuración", el estado de la pestaña activa se sincronizará con la URL (ej. `/connections?tab=whatsapp`). Esto permite compartir enlaces directos y mantener la posición al recargar.
*   **Estado Activo:** La pestaña seleccionada tendrá un fondo gris suave (`bg-muted`), indicando claramente la selección.
*   **Contenido:** Todas las pestañas mostrarán un componente estandarizado `PlaceholderContent` con el mensaje "Próximamente", listo para ser reemplazado por la lógica real en el futuro.

## 4. Plan de Implementación
1.  **Modificar `app-sidebar.tsx`:** Insertar el item "Conexiones".
2.  **Crear `src/app/(dashboard)/connections/page.tsx`:** Implementar la lógica de la página, importando los componentes de UI necesarios (`Tabs`, `Card`, Iconos).
3.  **Implementar Navegación por Grupos:** Estructurar la lista de pestañas (`TabsList`) insertando separadores/títulos entre los grupos de `TabsTrigger`.

¿Estás de acuerdo con esta estructura y los iconos propuestos para proceder con la implementación?