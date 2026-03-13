"use client";

import { useState, useEffect } from "react";
import { useForm, Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { OfferSchema, OfferFormValues } from "../../types/schema";
import { OfferStatus } from "../../types";
import { useOffer } from "../../hooks/use-offer";
import { OfferStudioLayout } from "../container/offer-studio-layout";
import { OfferLivePreview } from "./offer-live-preview";
import { OfferEditSheetManager } from "./offer-edit-sheet-manager";
import { Loader2, ArrowLeft } from "lucide-react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export function OfferEditor({ offerId }: { offerId: string }) {
  const router = useRouter();
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

  // Sync form with loaded data
  useEffect(() => {
    if (formValues) {
      form.reset(formValues);
    }
  }, [formValues, form]);

  const handleSave = async () => {
      const data = form.getValues();
      try {
          await saveOffer(data);
      } catch (e) {
          // Error handled in hook
      }
  };

  const handleSectionSave = async (sectionId: string) => {
      try {
          if (saveSection) {
             await saveSection(sectionId, form.getValues());
          } else {
             await saveOffer(form.getValues());
          }
      } catch (e) {
          // Error handled in hook
      }
  };

  if (loading) {
    return (
        <div className="flex h-screen items-center justify-center bg-background">
            <Loader2 className="animate-spin h-8 w-8 text-primary" />
        </div>
    );
  }

  if (error || !offer) {
      return (
          <div className="flex flex-col items-center justify-center h-screen gap-4 bg-background">
              <div className="text-destructive font-medium">{error || "Oferta no encontrada"}</div>
              <Link href={`/${tenantId}/offer-studio`}>
                  <Button variant="outline"><ArrowLeft className="mr-2 h-4 w-4" /> Volver al Studio</Button>
              </Link>
          </div>
      );
  }

  return (
    <OfferStudioLayout
        offer={offer}
        onUpdate={handleSave}
        activeSection={activeSection || ""}
        onNavigate={setActiveSection}
        isSaving={saving}
    >
        <OfferLivePreview 
            form={form} 
            onEdit={setEditingSection} 
        />
        
        <OfferEditSheetManager 
            sectionId={editingSection}
            isOpen={!!editingSection}
            onClose={() => setEditingSection(null)}
            form={form}
            onSave={handleSectionSave}
            isSaving={saving}
        />
    </OfferStudioLayout>
  );
}
