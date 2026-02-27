I will restructure the `SalesPage` to replicate the "Connections" vertical tabs layout.

**Step 1: Component Extraction & Setup**

* Create a `PlaceholderContent` component (reused from `ConnectionsPage`) for the "Proximamente" states.

* Extract the current calendar and appointment logic into a new component named `AppointmentsView` within the same file. This ensures the complex calendar logic remains isolated and clean.

**Step 2: Implement Vertical Tabs Layout**

* Rebuild the main `SalesPage` structure using `Tabs` with a vertical sidebar layout, matching `ConnectionsPage`.

* **Sidebar Groups:**

  * **Citas:**

    * "Tipo de Cita" (Icon: `Settings2`) -> Shows "Proximamente"

    * "Disponibilidad" (Icon: `Clock`) -> Shows "Proximamente"

    * "Reservas" (Icon: `CalendarDays`) -> Shows nested content

  * **Ventas:**

    * "Pagos" (Icon: `CreditCard`) -> Shows "Proximamente"

**Step 3: Implement Nested Horizontal Tabs (Reservas)**

* Inside the "Reservas" tab, implement a secondary horizontal `Tabs` component.

* **Tabs:**

  * "Próximamente" -> Renders the extracted `AppointmentsView` (Current functionality).

  * "Sin confirmar" -> Shows "Próximamente".

  * "Pasado" -> Shows "Próximamente".

  * "Cancelado" -> Shows "Próximamente".

**Step 4: Cleanup & State**

* Ensure `useSearchParams` is used to manage tab state (optional but consistent with Connections).

* Verify all imports (Icons from `lucide-react`, UI components).

