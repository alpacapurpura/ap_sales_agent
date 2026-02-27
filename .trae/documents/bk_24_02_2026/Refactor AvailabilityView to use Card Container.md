I will update `frontend/src/components/sales/availability-view.tsx` to wrap the entire view in a `Card` container, matching the style of the "Reservas" tab.

**Implementation Steps:**

1.  **Modify `AvailabilityView` component:**
    *   Replace the outer `div` (className="space-y-6") with a `Card`.
    *   Move the existing header logic (Title "Disponibilidad" and "Nuevo" button) into a `CardHeader` component.
    *   Use `CardTitle` with the `Clock` icon and `CardDescription` for the header text.
    *   Place the "Nuevo" button inside the `CardHeader` (using flexbox to position it to the right).
    *   Wrap the content (loading state, list of schedules, empty state) inside `CardContent`.
    *   Ensure the `Sheet` component remains available (either outside or inside the Card, logically inside is fine for React structure).

**Outcome:**
The "Disponibilidad" tab will now display a unified Card container with a header and content area, consistent with the "Reservas" tab in the Sales dashboard.
