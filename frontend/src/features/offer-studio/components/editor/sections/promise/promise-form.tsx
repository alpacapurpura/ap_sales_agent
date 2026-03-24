"use client";

import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { RichSelect } from "@/components/ui/rich-select";
import { ACCESS_DURATION_METADATA } from "../../../../types/enum-metadata";
import { AccessDuration } from "../../../../types";
import { Sparkles, Clock } from "lucide-react";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

const PromiseSchema = OfferSchema.pick({
  headline_promise: true,
  primary_outcome: true,
  time_to_value: true,
  access_duration: true,
  access_duration_text: true
});

type PromiseFormValues = Pick<OfferFormValues, "headline_promise" | "primary_outcome" | "time_to_value" | "access_duration" | "access_duration_text">;

export interface PromiseFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
}

function PromiseContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <div className="space-y-6">
        <Card className="border-amber-200/50 dark:border-amber-800/30 bg-amber-50/30 dark:bg-amber-950/10">
            <CardContent className="pt-6 space-y-4">
                <FormField control={form.control} name="headline_promise" render={({ field }) => (
                    <FormItem>
                        <FormLabel className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                            <Sparkles className="w-4 h-4" /> La Gran Promesa (Headline)
                        </FormLabel>
                        <WithCopilot fieldId="headline_promise" fieldLabel="La Gran Promesa" getValue={() => field.value || ""}>
                          <FormControl>
                              <Textarea
                                  className="text-lg font-medium resize-none bg-background min-h-[100px]"
                                  placeholder="Te ayudo a lograr [Resultado] en [Tiempo] sin [Dolor]..."
                                  {...field}
                                  value={field.value || ""}
                              />
                          </FormControl>
                        </WithCopilot>
                        <FormMessage />
                    </FormItem>
                )} />
                <div className="grid grid-cols-2 gap-4">
                    <FormField control={form.control} name="primary_outcome" render={({ field }) => (
                        <FormItem>
                            <FormLabel>Resultado Tangible</FormLabel>
                            <WithCopilot fieldId="primary_outcome" fieldLabel="Resultado Tangible" getValue={() => field.value || ""}>
                              <FormControl><Input placeholder="Ej. $10k/mes" {...field} className="bg-background" /></FormControl>
                            </WithCopilot>
                        </FormItem>
                    )} />
                    <FormField control={form.control} name="time_to_value" render={({ field }) => (
                        <FormItem>
                            <FormLabel>Tiempo al Valor</FormLabel>
                            <FormControl><Input placeholder="Ej. 90 días" {...field} className="bg-background" /></FormControl>
                        </FormItem>
                    )} />
                </div>
                {/* Access Duration Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                    <FormField control={form.control} name="access_duration" render={({ field }) => (
                        <FormItem>
                            <FormLabel className="flex items-center gap-2">
                                <Clock className="w-4 h-4" /> Duración del Acceso
                            </FormLabel>
                            <RichSelect 
                                options={Object.entries(ACCESS_DURATION_METADATA).map(([k, v]) => ({ value: k, label: v.label, description: v.description }))}
                                value={field.value || undefined}
                                onValueChange={field.onChange}
                                placeholder="Selecciona duración..."
                            />
                            <FormMessage />
                        </FormItem>
                    )} />
                    
                    {(form.watch("access_duration") === AccessDuration.LIMITED_TIME_ACCESS || form.watch("access_duration") === AccessDuration.HYBRID_ACCESS) && (
                        <div className="animate-in fade-in slide-in-from-left-2">
                                <FormField control={form.control} name="access_duration_text" render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Tiempo Específico</FormLabel>
                                    <FormControl><Input placeholder="Ej. 1 Año, 6 Meses..." {...field} value={field.value || ""} className="bg-background" /></FormControl>
                                    <FormMessage />
                                </FormItem>
                            )} />
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    </div>
  );
}

export function PromiseForm({ defaultValues: propValues, onSave }: PromiseFormProps) {
  const defaultValues: PromiseFormValues = {
    headline_promise: propValues?.headline_promise || "",
    primary_outcome: propValues?.primary_outcome || "",
    time_to_value: propValues?.time_to_value || "",
    access_duration: propValues?.access_duration || AccessDuration.LIFETIME_CONTENT,
    access_duration_text: propValues?.access_duration_text || ""
  };

  const handleSave = async (data: PromiseFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<PromiseFormValues>
      schema={PromiseSchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <PromiseContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
