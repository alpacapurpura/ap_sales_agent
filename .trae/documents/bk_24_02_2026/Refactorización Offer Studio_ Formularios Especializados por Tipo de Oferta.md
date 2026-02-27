# Confirmación y Plan: Eliminación del Wizard y Adopción de Formularios Especializados

Entiendo perfectamente tu preocupación. El "Wizard genérico" no es el enfoque correcto para un sistema que distingue claramente entre 4 tipos de ofertas con naturalezas divergentes. Un Producto Físico (stock, envíos) no tiene nada que ver con una Mentoría (syllabus, llamadas) o una Suscripción (ciclos de facturación).

**Tu diagnóstico es correcto:**
1.  **Descartar el Wizard de "Nuevo Activo"**: Genera fricción y ambigüedad.
2.  **Modelos Especializados**: La base de datos y el backend **YA están preparados** para esto (verificamos `OfferType`, `ProductDetails`, `ServiceDetails` en los schemas y la columna `specific_details` en la DB).
3.  **Frontend Especializado**: Debemos exponer formularios dedicados para cada tipo desde el inicio.

---

## Plan de Ejecución Inmediata

### 1. Eliminación del Wizard Genérico
*   Eliminar la ruta `/offer-studio/new` que usa el Wizard.
*   Eliminar el componente `OfferWizard` para limpiar el código.

### 2. Creación de Formularios Especializados (The "Factory" Pattern)
En lugar de un "Wizard", crearemos 4 componentes de formulario independientes que hereden lógica común pero expongan UX específica:

*   `ProductForm`: Enfocado en logística (Stock, Envíos, Descargas).
*   `ServiceForm`: Enfocado en capacidad humana (Cupos, Timeline, Entregables).
*   `ProgramForm`: Enfocado en transformación educativa (Syllabus, Calendario).
*   `SubscriptionForm`: Enfocado en retención (Niveles, Facturación).

### 3. Rediseño del Dashboard (Acción Directa)
En el Dashboard de Offer Studio, el botón "Nueva Oferta" **ya no será genérico**.
*   Tab **Productos** -> Botón "Nuevo Producto" -> Abre Modal/Página `ProductForm`.
*   Tab **Servicios** -> Botón "Nuevo Servicio" -> Abre Modal/Página `ServiceForm`.
*   (Idem para los otros tabs).

### 4. Refactorización del Editor (`OfferEditor`)
El editor actual usa Tabs genéricos. Lo adaptaremos para que cargue el "Formulario Especializado" correspondiente según el tipo de oferta, manteniendo la consistencia visual pero cambiando los campos críticos.

## Resultado Final Esperado
Al entrar al tab "Servicios" y dar click en "Nuevo Servicio", verás inmediatamente campos como "Capacidad Máxima" y "Timeline de Onboarding", sin pasar por preguntas irrelevantes sobre stock o envíos. Esto alinea el Frontend con la realidad de tu Negocio.

¿Procedemos a desmantelar el Wizard y construir estos 4 pilares especializados?