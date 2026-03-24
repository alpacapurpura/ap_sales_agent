"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { OfferType } from "../../../../types";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RichSelect } from "@/components/ui/rich-select";
import { OFFER_TYPE_METADATA } from "../../../../types/offer-metadata";
import { Target } from "lucide-react";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";
import { avatarApi, Avatar } from "@/lib/api/avatar";

// Define partial schema for Strategy
const StrategySchema = OfferSchema.pick({
  public_name: true,
  type: true,
  avatar_id: true
});

type StrategyFormValues = Pick<OfferFormValues, "public_name" | "type" | "avatar_id">;

export interface StrategyFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any; // To satisfy OfferEditSheetManager passing 'form'
}

function StrategyContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const { getToken } = useAuth();
  const [avatars, setAvatars] = useState<Avatar[]>([]);

  useEffect(() => {
    const fetchAvatars = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await avatarApi.listAvatars(token);
        setAvatars(data);
      } catch (error) {
        console.error("Failed to load avatars", error);
      }
    };
    fetchAvatars();
  }, [getToken]);

  const offerTypeOptions = Object.values(OFFER_TYPE_METADATA).map(meta => ({
      value: meta.type,
      label: meta.label,
      description: meta.hint
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
            <FormField control={form.control} name="public_name" render={({ field }) => (
                <FormItem>
                    <FormLabel>Nombre Público</FormLabel>
                    <WithCopilot fieldId="offer_public_name" fieldLabel="Nombre de la Oferta" getValue={() => field.value || ""}>
                      <FormControl><Input {...field} value={field.value || ''} className="bg-background" /></FormControl>
                    </WithCopilot>
                    <FormMessage />
                </FormItem>
            )} />
            <FormField control={form.control} name="type" render={({ field }) => (
                <FormItem>
                    <FormLabel>Tipo de Oferta</FormLabel>
                    <RichSelect 
                        options={offerTypeOptions} 
                        value={field.value} 
                        onValueChange={field.onChange} 
                        disabled={!!field.value}
                    />
                    <FormMessage />
                </FormItem>
            )} />
        </div>

        {/* Avatar Selector directly in context */}
        <FormField control={form.control} name="avatar_id" render={({ field }) => (
            <FormItem className="md:col-span-1">
                <FormLabel className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-primary" /> Avatar Match
                </FormLabel>
                <RichSelect 
                    options={avatars.map(a => ({ 
                        value: a.id, 
                        label: a.name, 
                        description: a.icp_description ? a.icp_description.substring(0, 60) + "..." : "Sin descripción" 
                    }))} 
                    value={field.value || undefined} 
                    onValueChange={field.onChange} 
                    placeholder="Selecciona Avatar..."
                />
                <FormDescription className="text-xs">
                    ¿A quién le vendes? Define la psicología de la oferta.
                </FormDescription>
                <FormMessage />
            </FormItem>
        )} />
    </div>
  );
}

export function StrategyForm({ defaultValues: propValues, onSave }: StrategyFormProps) {
  // Filter relevant values
  const defaultValues: StrategyFormValues = {
    public_name: propValues?.public_name || "",
    type: propValues?.type || OfferType.GROUP_COACHING_PROGRAM,
    avatar_id: propValues?.avatar_id || ""
  };

  const handleSave = async (data: StrategyFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<StrategyFormValues>
      schema={StrategySchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <StrategyContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
