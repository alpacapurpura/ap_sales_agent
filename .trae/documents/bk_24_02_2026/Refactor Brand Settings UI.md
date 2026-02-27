Refactor "Sobre la Marca" page to use vertical tabs with new grouping.

1. **Modify** **`frontend/src/app/(dashboard)/brand-settings/page.tsx`**:

   * Import `PlaceholderContent` pattern (local definition) and Lucide icons (`Building2`, `Phone`, `Award`, `Users`, `Brain`, `Sparkles`).

   * Update the page layout to use a flexible container (`flex-col lg:flex-row`) with a sidebar for tabs, matching the "Ventas" page structure.

   * Reorganize tabs into two groups:

     * **Global**:

       * "Información Corporativa" (Icon: `Building2`, Content: `BrandIdentityForm`)

       * "Datos de Contacto" (Icon: `Phone`, Content: `ContactDataForm`)

     * **Marca**:

       * "Autoridad y Equipo" (Icon: `Award`, Content: `AuthoritySquadForm`)

       * "Avatares" (Icon: `Users`, Content: `PlaceholderContent` "Proximamente")

       * "Personalidad IA" (Icon: `Brain`, Content: `PlaceholderContent` "Proximamente")

   * Ensure the `Tabs` component uses the new vertical orientation style (`flex-col` in `TabsList` inside `aside`).

2. **Verify**:

   * Check that the page renders without errors.

   * Verify that all forms (Identity, Contact, Authority) are still accessible and functional in their new locations.

   * Confirm the visual layout matches the "Ventas" page (sidebar on left, content on right).

