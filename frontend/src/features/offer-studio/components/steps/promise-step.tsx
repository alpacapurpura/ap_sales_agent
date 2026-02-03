import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface StepProps {
  form: UseFormReturn<OfferFormValues>;
}

export function PromiseStep({ form }: StepProps) {
  return (
    <>
      <FormField
        control={form.control}
        name="headline_promise"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Gran Promesa (Headline)</FormLabel>
            <FormControl>
              <Textarea 
                placeholder="Te ayudo a escalar a 10k en 90 días sin ads..." 
                className="resize-none" 
                {...field} 
                value={field.value ?? ""}
              />
            </FormControl>
            <FormDescription>El gancho principal que usa el agente.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="primary_outcome"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Resultado Tangible</FormLabel>
              <FormControl>
                <Input placeholder="Sistema de ventas instalado" {...field} value={field.value ?? ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="time_to_value"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tiempo al Valor</FormLabel>
              <FormControl>
                <Input placeholder="3 semanas" {...field} value={field.value ?? ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={form.control}
        name="target_avatar_match"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Avatares Objetivo</FormLabel>
            <FormControl>
              {/* TODO: Multi-select component connecting to Avatar Definitions */}
              <Input placeholder="AGENCY_OWNER, COACH (Separados por coma)" 
                value={(field.value || []).join(", ")}
                onChange={(e) => field.onChange(e.target.value.split(",").map(s => s.trim()))}
              />
            </FormControl>
            <FormDescription>IDs de los avatares compatibles.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  );
}
