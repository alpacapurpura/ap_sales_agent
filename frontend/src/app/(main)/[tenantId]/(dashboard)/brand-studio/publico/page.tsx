import { BuyerPersonasLandingPage } from "@/features/brand-studio/pages/BuyerPersonasLandingPage";

/**
 * Buyer personas landing — shows the BuyerPersonaInstancePicker (col 2) plus
 * a welcome pane. Selecting or creating a persona routes to
 * /{tenantId}/brand-studio/publico/persona/{id}, where the 4-column Finder
 * layout activates (PersonaDetailPage).
 */
export default function BrandStudioPublicoPage() {
  return <BuyerPersonasLandingPage />;
}
