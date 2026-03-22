"use client";

import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

const OfferEditor = dynamic(
  () => import("@/features/offer-studio/components/editor/offer-editor").then((mod) => mod.OfferEditor),
  { 
    ssr: false,
    loading: () => (
      <div className="flex h-screen items-center justify-center bg-background">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    )
  }
);

export function OfferEditorClient({ offerId }: { offerId: string }) {
  return <OfferEditor offerId={offerId} />;
}
