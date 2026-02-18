"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { SectionProps } from "../../types/section";
import { OfferPsychologyCard } from "../cards/offer-psychology-card";
import { offerApi } from "@/features/offer-studio/api";

export function PsychologySection({ form }: SectionProps) {
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
