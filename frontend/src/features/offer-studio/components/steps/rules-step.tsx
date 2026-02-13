import { UseFormReturn, useFieldArray } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { GuaranteeType, FinancialCapacity } from "../../types";
import { Plus, Trash2, RefreshCcw } from "lucide-react";

interface StepProps {
  form: UseFormReturn<OfferFormValues>;
}

export function RulesStep({ form }: StepProps) {
  // Use generic field array for prerequisites string array
  // Note: React Hook Form useFieldArray works best with objects, for simple strings we might need a wrapper or manual management
  // But we can use a workaround or just manage via state if simpler. 
  // Let's stick to simple manual array management for strings to avoid object wrapper complexity in schema
  
  const prerequisites = form.watch("prerequisites") || [];

  const addPrerequisite = () => {
    const current = form.getValues("prerequisites") || [];
    form.setValue("prerequisites", [...current, ""]);
  };

  const removePrerequisite = (index: number) => {
    const current = form.getValues("prerequisites") || [];
    form.setValue("prerequisites", current.filter((_, i) => i !== index));
  };

  const updatePrerequisite = (index: number, value: string) => {
    const current = form.getValues("prerequisites") || [];
    current[index] = value;
    form.setValue("prerequisites", [...current]); // Trigger re-render
  };

  const loadGlobalPrerequisites = () => {
    // Mock Global Inheritance
    form.setValue("prerequisites", [
      "Debe tener un negocio activo",
      "Disponibilidad de 5h semanales",
      "Mentalidad de inversión (no gasto)"
    ]);
  };

  return (
    <div className="space-y-8">
      {/* Gatekeeping */}
      <div className="space-y-4 border-b pb-6">
        <h3 className="text-lg font-medium">Requisitos de Acceso (Gatekeeping)</h3>
        
        <FormField
          control={form.control}
          name="requires_application"
          render={({ field }) => (
            <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <FormLabel className="text-base">Requiere Aplicación</FormLabel>
                <FormDescription>
                  Si está activo, el agente no enviará link de pago, sino agendará llamada.
                </FormDescription>
              </div>
              <FormControl>
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="min_financial_capacity"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Capacidad Financiera Mínima (Filtro)</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona capacidad" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.values(FinancialCapacity).map((cap) => (
                    <SelectItem key={cap} value={cap}>{cap}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>Debe coincidir con la clasificación del Lead.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <FormLabel>Prerrequisitos (Checklist del Agente)</FormLabel>
            <div className="flex gap-2">
               <Button type="button" variant="ghost" size="sm" onClick={loadGlobalPrerequisites}>
                <RefreshCcw className="w-3 h-3 mr-1" /> Heredar Globales
              </Button>
              <Button type="button" variant="outline" size="sm" onClick={addPrerequisite}>
                <Plus className="w-3 h-3 mr-1" /> Agregar
              </Button>
            </div>
          </div>
          {prerequisites.map((req, index) => (
            <div key={index} className="flex gap-2">
              <Input 
                value={req} 
                onChange={(e) => updatePrerequisite(index, e.target.value)}
                placeholder={`Requisito ${index + 1}`}
              />
              <Button type="button" variant="ghost" size="icon" onClick={() => removePrerequisite(index)}>
                <Trash2 className="w-4 h-4 text-destructive" />
              </Button>
            </div>
          ))}
          {prerequisites.length === 0 && (
            <p className="text-sm text-muted-foreground italic">No hay requisitos definidos.</p>
          )}
        </div>
      </div>

      {/* Guarantee */}
      <div className="space-y-4 border-b pb-6">
        <h3 className="text-lg font-medium">Garantía y Riesgo</h3>
        <div className="grid grid-cols-2 gap-4">
           <FormField
            control={form.control}
            name="guarantee_type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Tipo de Garantía</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {Object.values(GuaranteeType).map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
         <FormField
            control={form.control}
            name="guarantee_terms"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Términos Legales/Ventas</FormLabel>
                <FormControl>
                  <Textarea placeholder="Si no consigues X en Y tiempo..." {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
      </div>

      {/* Downsell Logic */}
      <div>
        <h3 className="text-lg font-medium">Estrategia de Downsell</h3>
         <FormField
            control={form.control}
            name="downsell_offer_id"
            render={({ field }) => (
              <FormItem className="mt-4">
                <FormLabel>Oferta de Respaldo (Si dicen &quot;Muy caro&quot;)</FormLabel>
                <FormControl>
                  <Input placeholder="UUID del producto Downsell" {...field} />
                </FormControl>
                <FormDescription>El agente pivotará a esta oferta automáticamente.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
      </div>
    </div>
  );
}
