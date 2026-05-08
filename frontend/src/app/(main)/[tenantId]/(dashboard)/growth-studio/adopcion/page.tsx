import { StageDispatcher } from "@/features/growth-studio/pages/StageDispatcher";

export const metadata = {
  title: "Adopción | Growth Studio",
};

/**
 * Server Component thin delegate para la etapa Adopción.
 * Delega la carga lazy al StageDispatcher (Client Component).
 */
export default function AdopcionPage() {
  return <StageDispatcher slug="adopcion" />;
}
