# Esquema de Guardado y Plan de Implementación

Para resolver la falta de persistencia en el módulo "Resumen de la Oferta" y mantener una UX sencilla y consistente, propongo el siguiente esquema e implementación.

## Propuesta UX/UI
**Ubicación del Botón:**
Implementar un botón de acción primaria **"Guardar Cambios"** en la esquina superior derecha del área de contenido de cada pestaña (justo al lado del título "Resumen de la Oferta").

**Comportamiento:**
1.  **Estado Inicial:** Botón habilitado (o deshabilitado si no hay cambios, opcionalmente).
2.  **Al Clicar:**
    -   Muestra estado de carga ("Guardando...").
    -   Envía los datos al backend.
    -   Muestra una notificación (Toast) de éxito: "Oferta actualizada correctamente".
3.  **Feedback Visual:** Inputs controlados que reflejan el estado real de los datos.

Este enfoque es más sencillo y robusto que un botón global en el layout, ya que cada pestaña maneja contextos de datos muy diferentes (Resumen vs. Avatar vs. Objeciones).

---

## Plan de Implementación Técnica

### 1. Backend (FastAPI + SQLAlchemy)
Habilitar los endpoints necesarios para leer y actualizar ofertas.

*   **Crear Repositorio:** `src/services/db/repositories/product.py` para manejar operaciones CRUD de la tabla `Product`.
*   **Crear Router:** `src/api/routers/products.py` con:
    -   `GET /products/{product_id}`: Para cargar los datos iniciales.
    -   `PATCH /products/{product_id}`: Para guardar los cambios parciales (Nombre, Precio, Promesa).
*   **Integración:** Registrar el nuevo router en `src/api/routes.py`.

### 2. Frontend (Next.js + React Query)
Conectar la interfaz "dummy" actual con la API real.

*   **Cliente API:** Actualizar `src/lib/api/offer.ts` para reemplazar los mocks con llamadas reales (`fetch` o `axios`) a los nuevos endpoints.
*   **Gestión de Estado (Hook):**
    -   Refactorizar `offer/[id]/page.tsx` para usar un componente cliente (`OfferSummaryForm`).
    -   Implementar `React Hook Form` para el manejo eficiente del formulario.
    -   Usar `useMutation` (o `useState` + `useEffect`) para manejar la carga y el guardado.
*   **Interfaz:**
    -   Añadir el botón `Button` de Shadcn UI en el header del formulario.
    -   Integrar notificaciones `toast` para feedback de usuario.

### Estructura de Archivos Afectados
1.  `backend/src/services/db/repositories/product.py` (Nuevo)
2.  `backend/src/api/routers/products.py` (Nuevo)
3.  `backend/src/api/routes.py` (Modificar)
4.  `frontend/src/lib/api/offer.ts` (Modificar)
5.  `frontend/src/app/(dashboard)/offer-studio/offer/[id]/page.tsx` (Refactorizar a Client Component)
