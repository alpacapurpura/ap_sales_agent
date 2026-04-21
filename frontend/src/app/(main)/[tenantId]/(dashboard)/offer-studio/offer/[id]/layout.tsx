"use client";

import { use } from "react";

import { OfferShellLayout } from "@/features/offer-studio/components/OfferShellLayout";

/**
 * Persistent offer studio layout (F4 canonical).
 *
 * Mounts `OfferShellLayout` once per offer. Next.js preserves this tree while
 * `children` swap between tabs — tab switches don't re-mount the header.
 *
 * No React context: children read offer + counts via React Query (`useOffer`,
 * `useOfferCounts`). See `.claude/rules/frontend-fsd.md` — per-route state lives
 * in URL + React Query, never in a global shell context.
 */
export default function OfferLayout({
  params,
  children,
}: {
  params: Promise<{ tenantId: string; id: string }>;
  children: React.ReactNode;
}) {
  const { tenantId, id: offerId } = use(params);
  return (
    <OfferShellLayout offerId={offerId} tenantId={tenantId}>
      {children}
    </OfferShellLayout>
  );
}
