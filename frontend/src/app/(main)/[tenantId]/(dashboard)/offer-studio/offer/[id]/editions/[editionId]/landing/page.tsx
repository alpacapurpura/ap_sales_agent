import Link from "next/link";

import { Button } from "@/components/ui/button";

export const metadata = {
  title: "Editor de Landing · Nicolify",
};

interface Params {
  tenantId: string;
  id: string;
  editionId: string;
}

/**
 * Full-screen landing editor route per edition (Phase 9e stub).
 *
 * The real Puck integration is scoped for a follow-up. Until it lands
 * this page is a deliberate placeholder so the `LandingSplitButton`
 * "Editar landing" main click always has a landing target — rather
 * than 404 — and so `window.open(...)` in the parent shell works
 * without surprises. The page intentionally lives outside the shell
 * grid so a future Puck canvas can span the full viewport.
 */
export default async function EditionLandingEditorPage({ params }: { params: Promise<Params> }) {
  const { tenantId, id, editionId } = await params;
  const backHref = `/${tenantId}/offer-studio/offer/${id}?edition=${editionId}`;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-muted/30 p-10">
      <div className="max-w-md space-y-3 rounded-2xl border bg-background p-8 text-center shadow-sm">
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-2xl">
          🚧
        </span>
        <h1 className="text-2xl font-bold">Editor de landing</h1>
        <p className="text-sm text-muted-foreground">
          El editor visual (estilo Puck) estará disponible en breve. Por ahora esta ruta funciona
          como landing target del split button del Offer Shell.
        </p>
        <p className="text-xs text-muted-foreground">
          Edición: <code className="font-mono">{editionId.slice(0, 8)}</code>
        </p>
        <div className="flex justify-center">
          <Link href={backHref}>
            <Button variant="outline">← Volver a la oferta</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
