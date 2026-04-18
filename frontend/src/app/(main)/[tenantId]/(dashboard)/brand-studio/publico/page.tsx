import { Card } from "@/components/ui/card";

/**
 * Buyer personas index. Thin server component — the per-persona list
 * lands in the next persona iteration. For now this is a placeholder card
 * directing the user to a direct persona URL (the sidebar links here, and
 * offer-studio deep-links /publico/persona/{id}/edit).
 */
export default async function BrandStudioPublicoPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  return (
    <div className="p-8">
      <h1 className="mb-2 text-2xl font-semibold">Buyer personas</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Perfiles arquetípicos que el SDR usa para segmentar. Seleccioná una persona o creá una
        nueva.
      </p>
      <Card className="p-6 text-sm text-muted-foreground">
        Catálogo en runtime. Navegá directo vía{" "}
        <code>/{tenantId}/brand-studio/publico/persona/[personaId]</code>.
      </Card>
    </div>
  );
}
