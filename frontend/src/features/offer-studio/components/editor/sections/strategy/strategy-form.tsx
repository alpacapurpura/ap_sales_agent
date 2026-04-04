"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { OfferArchetype } from "../../../../types";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RichSelect } from "@/components/ui/rich-select";
import { ARCHETYPE_METADATA } from "../../../../config/archetype-metadata";
import { Target } from "lucide-react";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";
import { avatarApi, Avatar } from "@/lib/api/avatar";

const EMPTY_AVATARS: Avatar[] = [];

// Define partial schema for Strategy
const StrategySchema = OfferSchema.pick({
  public_name: true,
  archetype: true,
  avatar_id: true
});

type StrategyFormValues = Pick<OfferFormValues, "public_name" | "archetype" | "avatar_id">;

export interface StrategyFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: UseFormReturn<OfferFormValues>;
}

function StrategyContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const { getToken } = useAuth();

  const { data: avatars = EMPTY_AVATARS } = useQuery({
    queryKey: ["avatars"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return avatarApi.listAvatars(token);
    },
    staleTime: 5 * 60 * 1000,
  });

  const archetypeOptions = Object.values(OfferArchetype).map(arch => {
    const meta = ARCHETYPE_METADATA[arch];
    return {
      value: arch,
      label: meta?.label || arch,
      description: meta?.subtitle || ""
    };
  });

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
            <FormField control={form.control} name="archetype" render={({ field }) => (
                <FormItem>
                    <FormLabel>Archetype de Oferta</FormLabel>
                    <RichSelect
                        options={archetypeOptions}
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
  const defaultValues: StrategyFormValues = {
    public_name: propValues?.public_name || "",
    archetype: propValues?.archetype || OfferArchetype.PRODUCTO,
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
