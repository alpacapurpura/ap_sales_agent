"use client";

import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { use } from "react";

import { Button } from "@/components/ui/button";
import { OfferShell } from "@/features/offer-studio/components/container/OfferShell";
import { useOffer } from "@/features/offer-studio/hooks/use-offer";
import { useOfferCounts } from "@/features/offer-studio/hooks/use-offer-counts";

/**
 * Persistent offer studio layout.
 *
 * Mounts the `<OfferShell />` (header rows + tab bar) once per offer. Next.js
 * preserves this tree while `children` swap between tabs — cambio de tab = 1
 * click, sin re-render del header.
 *
 * The route is a Client Component because Nicolify has no server-side Clerk
 * token helper wired up yet. Data flows through the same hooks the editor
 * already uses.
 */
export default function OfferLayout({
  params,
  children,
}: {
  params: Promise<{ tenantId: string; id: string }>;
  children: React.ReactNode;
}) {
  const { tenantId, id: offerId } = use(params);
  const { offer, loading: offerLoading, error: offerError } = useOffer(offerId);
  const { data: counts, isLoading: countsLoading, error: countsError } = useOfferCounts(offerId);

  if (offerLoading || countsLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
      </div>
    );
  }

  if (offerError || !offer) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background">
        <p className="font-medium text-destructive">{offerError ?? "Oferta no encontrada"}</p>
        <Link href={`/${tenantId}/offer-studio`}>
          <Button variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver al Studio
          </Button>
        </Link>
      </div>
    );
  }

  // Counts failure is non-fatal: render the shell with zeros and log.
  const safeCounts = counts ?? {
    assets: 0,
    campaigns: 0,
    knowledge: 0,
    active_campaigns: 0,
  };
  if (countsError) {
    console.warn("Failed to load offer counts", countsError);
  }

  return (
    <OfferShell offer={offer} counts={safeCounts} tenantId={tenantId}>
      {children}
    </OfferShell>
  );
}
