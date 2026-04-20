import { BuyerPersonasDashboard } from "@/features/brand-studio/components/dashboard/BuyerPersonasDashboard";

/**
 * Buyer personas studio. Server Component that delegates to the dashboard
 * client component (list + create flow + start-interview wiring).
 *
 * Route: /{tenantId}/brand-studio/publico
 */
export default function BrandStudioPublicoPage() {
  return <BuyerPersonasDashboard />;
}
