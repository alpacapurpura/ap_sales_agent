Voy a refactorizar la página principal de **Ecosistema de Ofertas** para que adopte la estructura de pestañas verticales idéntica a "Sobre la Marca".

### Cambios en `frontend/src/app/(dashboard)/offer-studio/page.tsx`:

1.  **Conversión a Client Component**: Se agregará `"use client"` para soportar la interactividad de los tabs.
2.  **Estructura Visual**: Se replicará el layout de `BrandSettingsPage` (Título, Descripción, Divisor, Sidebar con Tabs).
3.  **Implementación de Tabs Verticales**:
    *   **Grupo "Offer"**:
        *   **Productos**: Mostrará pantalla "Próximamente".
        *   **Servicios**: Aquí se moverá el contenido actual (`<OfferDashboard />`).
        *   **Programas**: Mostrará pantalla "Próximamente".
        *   **Suscripciones**: Mostrará pantalla "Próximamente".
4.  **Componentes**: Se reutilizarán los componentes UI de Shadcn (`Tabs`, `Card`) y Lucide Icons (`Package`, `Briefcase`, `GraduationCap`, `Repeat`) para mantener la consistencia visual.

El resultado será una interfaz unificada donde "Servicios" contiene la funcionalidad actual y las nuevas secciones quedan preparadas para el futuro.