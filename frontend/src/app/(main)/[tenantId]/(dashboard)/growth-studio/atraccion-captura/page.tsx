import { StageDispatcher } from "@/features/growth-studio/pages/StageDispatcher";

export const metadata = {
  title: "Atracción & Captura | Growth Studio",
};

/**
 * Server Component thin delegate para la etapa Atracción & Captura.
 * Delega la carga lazy al StageDispatcher (Client Component).
 */
export default function AtraccionCapturaPage() {
  return <StageDispatcher slug="atraccion-captura" />;
}
