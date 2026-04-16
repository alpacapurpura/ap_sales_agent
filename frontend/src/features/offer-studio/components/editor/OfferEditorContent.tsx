"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm, type Resolver } from "react-hook-form";

import { Button } from "@/components/ui/button";

import { useOffer } from "../../hooks/use-offer";
import { OfferStatus } from "../../types";
import { OfferSchema, type OfferFormValues } from "../../types/schema";
import { OfferNavRail } from "../navigation/OfferNavRail";

import { OfferEditSheetManager } from "./OfferEditSheetManager";
import { OfferLivePreview } from "./OfferLivePreview";

/**
 * Inner editor content rendered inside the persistent Offer Studio shell
 * (layout.tsx → OfferShell → this component).
 *
 * Unlike the legacy `OfferEditor`, this version does NOT wrap its children in
 * `<OfferStudioLayout>`. The new shell owns the header rows, tab bar, status
 * switcher, landing button, auto-save indicator and progress bar.
 *
 * TODO (Chunk 4): wire `useAutoSave` to `useOfferAutoSave().setSnapshot` so
 * the header indicator reflects in-flight saves. For this chunk, saves still
 * fire through `useOffer.saveSection`, but the indicator stays idle.
 */
export function OfferEditorContent({ offerId }: { offerId: string }) {
  const params = useParams();
  const tenantId = params?.tenantId as string;

  const { offer, formValues, loading, saving, error, saveOffer, saveSection } = useOffer(offerId);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [editingSection, setEditingSection] = useState<string | null>(null);

  const form = useForm<OfferFormValues>({
    resolver: zodResolver(OfferSchema) as Resolver<OfferFormValues>,
    defaultValues: {
      status: OfferStatus.DRAFT,
      requires_application: false,
      pricing_options: [],
      marketing_pain_points: [],
      marketing_desires: [],
      objections: [],
      prerequisites: [],
      includes_offers: [],
      deliverables: [],
    },
    mode: "onChange",
  });

  // Sync form with loaded data. `form.reset` is stable, so we depend on it
  // explicitly rather than on `form` (which is a new reference each render).
  const { reset: formReset } = form;
  useEffect(() => {
    if (formValues) {
      formReset(formValues);
    }
  }, [formValues, formReset]);

  const handleSectionSave = async (sectionId: string) => {
    try {
      if (saveSection) {
        await saveSection(sectionId, form.getValues());
      } else {
        await saveOffer(form.getValues());
      }
    } catch {
      // Error handled in hook
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
      </div>
    );
  }

  if (error || !offer) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 bg-background">
        <p className="font-medium text-destructive">{error ?? "Oferta no encontrada"}</p>
        <Link href={`/${tenantId}/offer-studio`}>
          <Button variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver al Studio
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-1 overflow-hidden" role="region" aria-label="Editor de oferta">
      <OfferNavRail
        offer={offer}
        activeSection={activeSection ?? ""}
        onNavigate={setActiveSection}
        className="z-20 h-full flex-none border-r bg-muted/10"
      />

      <main className="relative flex-1 overflow-y-auto scroll-smooth" id="offer-editor-main">
        <div className="min-h-full pb-20">
          <div className="mx-auto max-w-5xl p-8">
            <OfferLivePreview form={form} onEdit={setEditingSection} />
          </div>
        </div>

        <OfferEditSheetManager
          sectionId={editingSection}
          isOpen={!!editingSection}
          onClose={() => setEditingSection(null)}
          form={form}
          onSave={handleSectionSave}
          isSaving={saving}
        />
      </main>
    </div>
  );
}
