"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProgramType } from "../../types/index";

export function ProgramDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium">Estructura del Programa</h3>
      
      <FormField
        control={form.control}
        name="specific_details.program_type"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Tipo de Programa</FormLabel>
            <Select onValueChange={field.onChange} defaultValue={field.value as string}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                {Object.values(ProgramType).map((t) => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />
      
      <div className="grid grid-cols-2 gap-4">
           <FormField
            control={form.control}
            name="specific_details.duration_weeks"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Duración (Semanas)</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseInt(e.target.value))} value={field.value as number || 0} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
           <FormField
            control={form.control}
            name="specific_details.calls_per_week"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Llamadas Semanales</FormLabel>
                <FormControl>
                  <Input type="number" {...field} onChange={e => field.onChange(parseInt(e.target.value))} value={field.value as number || 0} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
      </div>

      <FormField
        control={form.control}
        name="specific_details.call_schedule_details"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Horario de Sesiones</FormLabel>
            <FormControl>
              <Input placeholder="Martes 19:00 EST y Jueves 12:00 EST" {...field} value={field.value as string || ""} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      
       <FormField
        control={form.control}
        name="specific_details.requirements_to_graduate"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Requisito de Graduación</FormLabel>
            <FormControl>
              <Input placeholder="Facturar primeros $5k" {...field} value={field.value as string || ""} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
}
