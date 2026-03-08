# Plan de Actualización de Documentación: Módulo de Ofertas (Offer/Product)

Este plan detalla los pasos para actualizar `docs/domains/module_offer.md` siguiendo el estándar de "Agent-Oriented Documentation". El objetivo es crear una fuente de verdad técnica para agentes de IA, explicando la arquitectura, el polimorfismo y la ubicación del código.

## Pasos de Implementación

1.  **Análisis del Contenido Actual**
    *   [x] Leer el archivo `docs/domains/module_offer.md` (si existe) para evaluar su estado actual.

2.  **Redacción de la Documentación (Agent-Oriented)**
    *   Estructurar el documento con las siguientes secciones:
        *   **Contexto del Agente**: Definición de la entidad como "Fuente de Verdad" para ventas.
        *   **1. Mapa de Código (The "Where")**:
            *   Backend: `Offer` (Domain), `ProductModel` (DB), `OfferRepository`, `Router`.
            *   Frontend: `useOffer` (Hook), `OfferEditor` (Component), `Schema` (Zod).
        *   **2. Lógica de Negocio (The "Why" & "How")**:
            *   **Polimorfismo Híbrido**: Explicar el uso de `type` como discriminador y `specific_details` (JSONB) para la flexibilidad. Detallar el mapeo `OFFER_TYPE_TO_DETAILS_MAPPING`.
            *   **Dualidad Offer/Product**: Aclarar que la entidad de dominio es `Offer` pero la tabla es `products`.
            *   **Pricing & Deliverables**: Explicar la estructura JSONB para listas complejas.
        *   **3. Casos Borde y Gotchas (Edge Cases)**:
            *   Validación de esquemas JSONB en tiempo de ejecución.
            *   Manejo de actualizaciones parciales en listas (Pricing).
            *   Mutación de ofertas activas y consistencia con agentes de ventas.
        *   **4. Snippets para Agentes**:
            *   Ejemplos de consultas polimórficas en Python.
            *   Ejemplo de discriminación de tipos en Frontend.

3.  **Verificación**
    *   Confirmar que los paths de archivos sean correctos y existan en el proyecto.
    *   Asegurar que la explicación del polimorfismo sea clara y técnica.

## Archivos Afectados
- `docs/domains/module_offer.md` (Escritura/Sobreescritura)
