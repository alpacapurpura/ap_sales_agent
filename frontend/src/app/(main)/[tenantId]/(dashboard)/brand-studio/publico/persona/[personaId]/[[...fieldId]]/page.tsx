import { PersonaDetailPage } from "@/features/brand-studio/pages/PersonaDetailPage";

/**
 * Buyer persona detail route.
 *
 *   /{tenantId}/brand-studio/publico/persona/{personaId}            → list view
 *   /{tenantId}/brand-studio/publico/persona/{personaId}/{fieldId}  → detail view
 *
 * The page itself reads `tenantId`, `personaId` and `fieldId` from the URL
 * via `useParams` — this route file stays thin.
 */
export default function BrandStudioPersonaPage() {
  return <PersonaDetailPage />;
}
