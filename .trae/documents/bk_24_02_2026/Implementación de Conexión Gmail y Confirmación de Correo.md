I will implement the custom confirmation button feature by updating the backend schema and frontend components.

**Backend (`backend/src/core/domain/event_type_schema.py`):**

1. Define a new Pydantic model `ConfirmationButtonConfig`:

   * `enabled: bool` (default False)

   * `text: str` (Optional, default "Volver al inicio")

   * `url: str` (Optional)
2. Add `confirmation_button: ConfirmationButtonConfig` to the `EventType` and `EventTypeUpdate` models.

**Frontend:**

1. **Sidebar (`frontend/src/components/sales/event-type-form.tsx`):**

   * Add a new section at the bottom for "Botón de Confirmación".

   * Include a `Checkbox` to toggle `enabled`.

   * If enabled, show `Input` fields for `text` (Label: "Texto del Botón") and `url` (Label: "Enlace de Redirección").

   * Update `formData` state handling to include this new nested object.
2. **Booking Page (`frontend/src/app/book/[tenant_slug]/[event_slug]/page.tsx`):**

   * Update the success view to read from `data.event_type.confirmation_button`.

   * If `enabled` is true:

     * Render the button with the configured `text`.

     * On click, redirect to `url` (using `window.location.href` or `router.push`).

   * If `enabled` is false (or null), do **not** render any button (as per "no debería aparecer ningun boton").

**Validation:**

* Verify the sidebar saves the config correctly.

* Verify the booking page reflects the changes immediately.

