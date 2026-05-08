import { StageDispatcher } from "@/features/growth-studio/pages/StageDispatcher";

export const metadata = {
  title: "Ventas | Growth Studio",
};

/**
 * Server Component thin delegate para la etapa Ventas.
 * Delega la carga lazy al StageDispatcher (Client Component).
 */
export default function VentasPage() {
  return <StageDispatcher slug="ventas" />;
}
