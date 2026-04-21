import { PersonaDetailPage } from "@/features/brand-studio/pages/PersonaDetailPage";

/**
 * Buyer persona detail route.
 *
 *   /{tenantId}/brand-studio/publico/persona/{personaId}                 → list view
 *   /{tenantId}/brand-studio/publico/persona/{personaId}?field={fieldId} → detail view
 *
 * The page reads `tenantId` + `personaId` from the URL via `useParams`;
 * the active field id lives in the `?field=` query param and is read
 * client-side via `useActiveField`.
 */
export default function BrandStudioPersonaPage() {
  return <PersonaDetailPage />;
}
