import { UseFormReturn, useFieldArray } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Plus, Trash2, DollarSign } from "lucide-react";

interface StepProps {
  form: UseFormReturn<OfferFormValues>;
}

export function PricingStep({ form }: StepProps) {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "pricing_options",
  });

  return (
    <div className="space-y-6">
      <FormField
        control={form.control}
        name="currency"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Moneda</FormLabel>
            <FormControl>
              <Input className="w-24" {...field} value={field.value || ""} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium">Opciones de Precio</h3>
            <p className="text-sm text-muted-foreground">Configura planes de pago y descuentos.</p>
          </div>
          <Button 
            type="button" 
            variant="outline" 
            size="sm"
            onClick={() => append({ 
              label: "", 
              total_amount: 0, 
              deposit_required: 0, 
              number_of_installments: 1, 
              installment_amount: 0, 
              is_default: false,
              savings_claim: "" 
            })}
          >
            <Plus className="w-4 h-4 mr-2" />
            Agregar Plan
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fields.map((field, index) => (
            <div key={field.id} className="border rounded-lg p-4 space-y-4 relative bg-card">
              <div className="absolute top-2 right-2">
                <Button type="button" variant="ghost" size="icon" onClick={() => remove(index)}>
                  <Trash2 className="w-4 h-4 text-destructive" />
                </Button>
              </div>

              <FormField
                control={form.control}
                name={`pricing_options.${index}.label`}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Etiqueta</FormLabel>
                    <FormControl>
                      <Input placeholder="Nombre del Plan" {...field} value={field.value || ""} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name={`pricing_options.${index}.total_amount`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Total ($)</FormLabel>
                      <FormControl>
                        <div className="relative">
                          <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                          <Input type="number" className="pl-8" {...field} onChange={e => field.onChange(parseFloat(e.target.value))} />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                 <FormField
                  control={form.control}
                  name={`pricing_options.${index}.savings_claim`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Claim de Ahorro</FormLabel>
                      <FormControl>
                         <Input placeholder="Ahorras $500" {...field} value={field.value || ""} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                 <FormField
                  control={form.control}
                  name={`pricing_options.${index}.deposit_required`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Depósito</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value))} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                 <FormField
                  control={form.control}
                  name={`pricing_options.${index}.number_of_installments`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Cuotas</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} onChange={e => field.onChange(parseInt(e.target.value))} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                 <FormField
                  control={form.control}
                  name={`pricing_options.${index}.installment_amount`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Monto/Cuota</FormLabel>
                      <FormControl>
                        <Input type="number" {...field} onChange={e => field.onChange(parseFloat(e.target.value))} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name={`pricing_options.${index}.is_default`}
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Opción Recomendada</FormLabel>
                      <FormDescription>
                        Esta será la primera opción que presente el agente.
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
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
