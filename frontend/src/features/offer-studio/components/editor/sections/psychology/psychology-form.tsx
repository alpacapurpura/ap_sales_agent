"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { UseFormReturn } from "react-hook-form";
import { toast } from "sonner";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { OfferPsychologyCard } from "../../components/cards/offer-psychology-card";
import { offerApi } from "@/features/offer-studio/api";

const PsychologySchema = OfferSchema.pick({
  marketing_pain_points: true,
  marketing_desires: true,
  avatar_id: true, // Needed for generation logic context
  public_name: true, // Needed for generation logic context
  headline_promise: true // Needed for generation logic context
});

type PsychologyFormValues = Pick<OfferFormValues, "marketing_pain_points" | "marketing_desires" | "avatar_id" | "public_name" | "headline_promise">;

export interface PsychologyFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
}

function PsychologyContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const { getToken } = useAuth();
  const [generatingPsychology, setGeneratingPsychology] = useState(false);

  const handleGeneratePsychology = async () => {
    const avatarId = form.getValues("avatar_id");
    const currentPains = form.getValues("marketing_pain_points") || [];
    const currentDesires = form.getValues("marketing_desires") || [];
    const offerName = form.getValues("public_name") || "Oferta sin nombre";
    const offerDesc = form.getValues("headline_promise");

    if (!avatarId) return;
    setGeneratingPsychology(true);

    try {
        const token = await getToken();
        if (!token) return;

        const result = await offerApi.generatePsychology({
            avatar_id: avatarId,
            offer_name: offerName,
            offer_description: offerDesc,
            current_pains: currentPains,
            current_desires: currentDesires
        }, token);

        // Replace with AI suggestions
        form.setValue("marketing_pain_points", result.pains as any);
        form.setValue("marketing_desires", result.desires as any);
        
        toast.success("Psicología generada con IA exitosamente");
    } catch (e) {
        toast.error("Error generando psicología con IA");
        console.error(e);
    } finally {
        setGeneratingPsychology(false);
    }
  };

  return (
    <OfferPsychologyCard 
        control={form.control}
        onGenerate={handleGeneratePsychology}
        avatarSelected={!!form.watch("avatar_id")}
        isGenerating={generatingPsychology}
    />
  );
}

export function PsychologyForm({ defaultValues: propValues, onSave }: PsychologyFormProps) {
  const defaultValues: PsychologyFormValues = {
    marketing_pain_points: propValues?.marketing_pain_points || [],
    marketing_desires: propValues?.marketing_desires || [],
    avatar_id: propValues?.avatar_id || "",
    public_name: propValues?.public_name || "",
    headline_promise: propValues?.headline_promise || ""
  };

  const handleSave = async (data: PsychologyFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<PsychologyFormValues>
      schema={PsychologySchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <PsychologyContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
