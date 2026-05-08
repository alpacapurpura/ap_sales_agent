import { StageDispatcher } from "@/features/growth-studio/pages/StageDispatcher";

export const metadata = {
  title: "Nutrición & Oportunidad | Growth Studio",
};

/**
 * Server Component thin delegate para la etapa Nutrición & Oportunidad.
 * Delega la carga lazy al StageDispatcher (Client Component).
 */
export default function NutricionOportunidadPage() {
  return <StageDispatcher slug="nutricion-oportunidad" />;
}
