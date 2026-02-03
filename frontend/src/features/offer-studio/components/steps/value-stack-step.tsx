import { UseFormReturn, useFieldArray } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DeliverableFormat } from "../../types/index";
import { Plus, Trash2 } from "lucide-react";

interface StepProps {
  form: UseFormReturn<OfferFormValues>;
}

export function ValueStackStep({ form }: StepProps) {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "deliverables",
  });

  return (
    <div className="space-y-8">
      {/* Modular Offers */}
      <FormField
        control={form.control}
        name="includes_offers"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Incluir otras Ofertas (Bundling)</FormLabel>
            <FormControl>
              <Input 
                placeholder="UUIDs de ofertas (separados por coma)" 
                value={field.value.join(", ")}
                onChange={(e) => field.onChange(e.target.value.split(",").map(s => s.trim()).filter(Boolean))}
              />
            </FormControl>
            <FormDescription>Si esta oferta incluye otras (ej. Curso Base + Taller).</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />

      {/* Deliverables Builder */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium">Entregables Específicos</h3>
            <p className="text-sm text-muted-foreground">Desglosa qué incluye exactamente (para el Stack de Valor).</p>
          </div>
          <Button 
            type="button" 
            variant="outline" 
            size="sm"
            onClick={() => append({ name: "", format: DeliverableFormat.RECORDED_CONTENT, quantity: "1", value_stack_price: 0 })}
          >
            <Plus className="w-4 h-4 mr-2" />
            Agregar Item
          </Button>
        </div>

        <div className="space-y-4">
          {fields.map((field, index) => (
            <div key={field.id} className="grid grid-cols-12 gap-4 items-end border p-4 rounded-lg bg-muted/20">
              <div className="col-span-4">
                <FormField
                  control={form.control}
                  name={`deliverables.${index}.name`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Nombre</FormLabel>
                      <FormControl>
                        <Input placeholder="Llamadas Q&A" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="col-span-3">
                <FormField
                  control={form.control}
                  name={`deliverables.${index}.format`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Formato</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {Object.values(DeliverableFormat).map((fmt) => (
                            <SelectItem key={fmt} value={fmt}>{fmt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="col-span-2">
                <FormField
                  control={form.control}
                  name={`deliverables.${index}.quantity`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Cantidad</FormLabel>
                      <FormControl>
                        <Input placeholder="12 sesiones" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="col-span-2">
                <FormField
                  control={form.control}
                  name={`deliverables.${index}.value_stack_price`}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs">Valor ($)</FormLabel>
                      <FormControl>
                        <Input 
                          type="number" 
                          {...field} 
                          onChange={e => field.onChange(parseFloat(e.target.value))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="col-span-1">
                <Button type="button" variant="ghost" size="icon" onClick={() => remove(index)}>
                  <Trash2 className="w-4 h-4 text-destructive" />
                </Button>
              </div>
            </div>
          ))}
          {fields.length === 0 && (
            <div className="text-center py-8 border-dashed border-2 rounded-lg text-muted-foreground">
              No hay entregables definidos.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
