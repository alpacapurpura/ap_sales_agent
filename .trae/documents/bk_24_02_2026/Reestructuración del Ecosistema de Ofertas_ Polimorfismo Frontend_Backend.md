# Plan de Reestructuración: Ecosistema de Ofertas Polimórfico

Este plan aborda tus dos preguntas: la visibilidad de los cambios en el frontend y la obsolescencia de los tabs actuales frente a la nueva lógica de negocio.

## 1. Respuesta a tus Preguntas

1.  **¿Dónde están los cambios?**: Los cambios previos (Wizard de 5 pasos) se crearon en `features/offer-studio/components/offer-wizard.tsx` y sus rutas, pero **no se conectaron a la navegación principal** ni a la página `offer-studio/page.tsx`. Por eso no los ves. Este plan conecta todo.
2.  **¿Están desactualizados los 4 Tabs?**: **No, al contrario**. La nueva lógica de "Clases Python" (Product, Service, Program, Subscription) es *exactamente* lo que justifica esos 4 tabs.
    *   **Antes**: Eran placeholders vacíos.
    *   **Ahora**: Cada tab instanciará una "Subclase" diferente de la Oferta, con campos únicos (ej: *Stock* para Productos vs *Syllabus* para Programas).

---

## 2. Arquitectura Backend: Polimorfismo sin Romper Nada

Implementaremos el patrón de "Herencia por Composición" usando Pydantic y una columna JSONB flexible. No haremos 4 tablas nuevas, sino una gestión inteligente de los datos específicos.

### A. Nuevos Enums (Vocabulario Controlado)
Actualizaremos `offer_enums.py` con:
*   `ProductFormat` (Digital/Físico)
*   `ServiceCapacity` (Open/Waitlist)
*   `ProgramType` (Evergreen/Cohort)
*   `BillingFrequency` (Monthly/Yearly)

### B. Esquema de Datos (Pydantic Discriminated Unions)
En `schema.py`, definiremos 4 modelos de detalle que "cuelgan" de la oferta principal:
*   `ProductDetails` (stock, shipping...)
*   `ServiceDetails` (deliverables, scope...)
*   `ProgramDetails` (syllabus, calls...)
*   `SubscriptionDetails` (billing, tier...)

La clase `Offer` tendrá un campo `specific_details` que se validará dinámicamente según el `OfferType`.

### C. Base de Datos
*   Agregar columna `specific_details` (JSONB) a la tabla `products`.
*   Migración segura que mantiene los datos existentes.

---

## 3. Frontend: Ecosistema Vivo

Haremos que cada Tab en `/offer-studio` sea funcional y cargue su tipo de oferta específico.

### A. Refactorización del Wizard (`OfferWizard`)
El Wizard actual es genérico. Lo transformaremos para que el **Paso 3 (Value Stack)** sea dinámico:
*   Si seleccionas "Producto" -> Muestra formulario de Stock/Envío.
*   Si seleccionas "Servicio" -> Muestra formulario de Capacidad/Alcance.
*   Si seleccionas "Programa" -> Muestra formulario de Syllabus/Calls.

### B. Conexión de Tabs
En `offer-studio/page.tsx`:
*   Tab **Productos** -> Lista ofertas tipo `DIGITAL_PRODUCT` o `PHYSICAL`. Botón "Nuevo Producto".
*   Tab **Servicios** -> Lista ofertas tipo `SERVICE_RETAINER` o `CONSULTING`. Botón "Nuevo Servicio".
*   Tab **Programas** -> Lista ofertas tipo `COHORT_PROGRAM` o `HYBRID_MENTORSHIP`. Botón "Nuevo Programa".
*   Tab **Suscripciones** -> Lista ofertas tipo `MEMBERSHIP`. Botón "Nueva Suscripción".

### C. Visualización de Cambios
Crearé una ruta de prueba o conectaré el botón "Nueva Oferta" existente para que lance el nuevo Wizard, permitiéndote ver y probar la creación de estos activos inmediatamente.

## 4. Ejecución
1.  **Backend**: Enums -> Schemas -> Model -> Migration.
2.  **Frontend Types**: Replicar interfaces TS.
3.  **Frontend UI**: Crear componente `SpecificDetailsForm` y conectarlo al Wizard.
4.  **Integración**: Actualizar el Dashboard para filtrar por tipo en cada tab.

