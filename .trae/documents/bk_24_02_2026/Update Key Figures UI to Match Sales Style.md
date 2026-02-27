I will update the "Personas Clave" (Key Figures) UI to match the "Tipos de Cita" (Appointment Types) style as requested.

### **Plan Details**

1.  **Target File**: `frontend/src/features/brand/components/key-figures-form.tsx`
2.  **Layout Change**:
    -   Switch from a 2-column grid (`md:grid-cols-2`) to a single-column stack (`grid gap-4`) to achieve the "Full Width" look.
3.  **Component Styling**:
    -   Replace the simple `div` container for each person with the Shadcn `Card` component.
    -   Apply the specific classes from Sales: `group cursor-pointer border hover:border-primary transition-all bg-background shadow-sm hover:shadow-md`.
    -   Structure the content using `CardContent` with flexbox layout (`flex-col sm:flex-row`).
4.  **Button Styling**:
    -   Group the **Edit** and **Delete** buttons into a unified control bar.
    -   Wrap them in a container: `border rounded-md bg-background`.
    -   Style individual buttons as `h-8 w-8 rounded-none border-r` to match the "joined" aesthetic.
    -   Ensure the Delete button retains its destructive color styling.

### **Outcome**
The "Personas Clave" section will look identical to the "Tipos de Cita" list: full-width cards with hover effects and a neat, bordered button group on the right.