import { OfferStudioNavRail } from "@/features/offer-studio/components/OfferStudioNavRail";

import type { ReactNode } from "react";

/**
 * Offer Studio editor sub-layout.
 *
 * Mirrors ``app/.../brand-studio/layout.tsx``: mounts the section ``NavRail``
 * as column 1 and lets the route page contribute the remaining Finder
 * columns (field list + field detail). Scoped to ``/editor/*`` so the rail
 * is only visible on the Info tab — Ventas / Assets / Campañas tabs render
 * under the parent shell without the section rail.
 *
 * The rail is self-contained — it reads ``tenantId`` + ``id`` from URL
 * params and fetches the offer via React Query (de-duped with the parent
 * shell query). No prop wiring.
 */
export default function OfferEditorLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-0 flex-1">
      <OfferStudioNavRail />
      <div className="flex min-w-0 flex-1">{children}</div>
    </div>
  );
}
