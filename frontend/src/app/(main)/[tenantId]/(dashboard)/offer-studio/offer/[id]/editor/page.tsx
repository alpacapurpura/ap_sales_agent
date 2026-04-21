import { ArrowRight } from "lucide-react";
import Link from "next/link";

/**
 * Offer Studio — editor landing page.
 *
 * Shown when the user lands on `/offer/{id}/editor` without a section.
 * Per the prototype `offer-editor.html`: display a centered welcome card
 * that drives the user to start with the "Promesa" section.
 *
 * TODO(F4): Once section-completion tracking is wired, redirect to the
 * first incomplete section instead of always showing this card.
 *
 * Server Component — no hooks needed.
 */
export default async function OfferEditorLandingPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string }>;
}) {
  const { tenantId, id } = await params;
  const promiseHref = `/${tenantId}/offer-studio/offer/${id}/editor/promise`;

  return (
    <div className="flex h-full items-center justify-center p-8">
      <div className="flex max-w-sm flex-col items-center gap-4 rounded-xl border bg-card p-8 text-center shadow-sm">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
          <ArrowRight className="h-6 w-6 text-primary" aria-hidden />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Tu oferta está lista</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Comienza definiendo la promesa central de tu oferta. Es el punto de partida que define
            todo lo demás.
          </p>
        </div>
        <Link
          href={promiseHref}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Empieza por Promesa
          <ArrowRight className="h-4 w-4" aria-hidden />
        </Link>
      </div>
    </div>
  );
}
