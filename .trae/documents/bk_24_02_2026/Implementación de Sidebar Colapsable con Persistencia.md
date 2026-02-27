
# Sidebar Colapsable (Estilo Moderno)

Implementaré la funcionalidad de colapsar el sidebar ("Collapsible Sidebar") para maximizar el espacio de trabajo, manteniendo la accesibilidad y el estilo visual.

## Propuesta de Diseño (Best Practices)

1.  **Botón de Toggle:** Añadiré un botón tipo "flecha" o "panel" (`PanelLeftClose`/`PanelLeftOpen`) en la cabecera del sidebar o en la parte inferior, que permita al usuario alternar entre modos.
2.  **Estado Persistente (Opcional pero recomendado):** Usaré un estado local (`isCollapsed`) para controlar el ancho.
3.  **Transiciones Suaves:** El sidebar transicionará suavemente de `w-64` (expandido) a `w-20` (colapsado).
4.  **Modo Iconos:**
    *   Cuando esté colapsado, los textos se ocultarán y solo se mostrarán los iconos centrados.
    *   Añadiré `Tooltips` (hover) para que el usuario sepa qué significa cada icono cuando no hay texto.
5.  **Ajuste del Layout Principal:** El `main` debe ajustar su `padding-left` dinámicamente (`md:pl-64` vs `md:pl-20`) basándose en el estado del sidebar.

## Plan de Implementación

1.  **Estado Global del Sidebar:** Moveré el estado de colapso a un contexto o lo elevaré al layout, pero para simplificar y mantenerlo rápido, usaré un **Contexto de UI** ligero o simplemente pasaré props si la estructura lo permite. Dado que el `Layout` y el `Sidebar` están separados, lo ideal es crear un pequeño contexto `SidebarContext` o usar almacenamiento local (`localStorage`) para recordar la preferencia del usuario.
2.  **Modificar `AppSidebar`:**
    *   Añadir botón de toggle.
    *   Lógica CSS condicional para ancho y visibilidad de texto.
3.  **Modificar `DashboardLayout`:**
    *   Necesita saber si el sidebar está colapsado para ajustar el margen del contenido.

*Refinamiento:* Para evitar complejidad excesiva con Contextos ahora mismo, puedo hacer que el Sidebar controle su propio estado y comunique el cambio, o usar una librería de estado simple como `zustand` si ya la tenemos, pero `localStorage` + estado local en un componente wrapper es lo más directo.

**Mejor opción (Simple & Efectiva):**
Crearé un `SidebarProvider` simple que envuelva el layout para compartir el estado `isCollapsed` entre el Sidebar y el área principal `main`.
