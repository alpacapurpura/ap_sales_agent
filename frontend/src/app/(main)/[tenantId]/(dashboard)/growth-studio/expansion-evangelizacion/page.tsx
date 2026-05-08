import { StageDispatcher } from "@/features/growth-studio/pages/StageDispatcher";

export const metadata = {
  title: "Expansión & Evangelización | Growth Studio",
};

/**
 * Server Component thin delegate para la etapa Expansión & Evangelización.
 * Delega la carga lazy al StageDispatcher (Client Component).
 */
export default function ExpansionEvangelizacionPage() {
  return <StageDispatcher slug="expansion-evangelizacion" />;
}
