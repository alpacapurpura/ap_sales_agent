import { useFieldArray } from "react-hook-form";
import { SectionProps } from "../../types/section";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DeliverableFormat } from "../../types";
import { Plus, Trash2, Layers, PackageOpen } from "lucide-react";
import { OffersMultiSelect } from "../ui/offers-multi-select";
import { DELIVERABLE_FORMAT_METADATA, getEnumOptions } from "../../types/enum-metadata";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";

export function ValueStackSection({ form }: SectionProps) {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "deliverables",
  });
  
  const currentOfferId = form.getValues().id;
  const formatOptions = getEnumOptions(DELIVERABLE_FORMAT_METADATA);

  return (
    <div className="space-y-8">
      {/* 1. Bundling / Modular Offers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-primary" />
            Ofertas Incluidas (Bundling)
          </CardTitle>
          <CardDescription>
            Si esta oferta es un paquete que incluye otros productos existentes (ej. Curso Base + Taller), selecciónalos aquí.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FormField
            control={form.control}
            name="includes_offers"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Seleccionar Ofertas</FormLabel>
                <FormControl>
                  <OffersMultiSelect 
                    value={field.value || []} 
                    onChange={field.onChange}
                    currentOfferId={currentOfferId}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </CardContent>
      </Card>

      {/* 2. Deliverables Builder (Stacked Layout) */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <PackageOpen className="h-5 w-5 text-primary" />
              Entregables Específicos
            </CardTitle>
            <CardDescription>
              Desglosa los componentes únicos de esta oferta que no son productos separados.
            </CardDescription>
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
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-4">
            {fields.map((field, index) => {
              const currentFormatValue = form.watch(`deliverables.${index}.format`);
              const selectedOption = formatOptions.find(opt => opt.value === currentFormatValue);

              return (
                <div key={field.id} className="group p-4 rounded-lg border bg-card hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors shadow-sm relative space-y-4">
                  
                  {/* Row 1: Name (Full Width) */}
                  <div className="w-full">
                    <FormField
                      control={form.control}
                      name={`deliverables.${index}.name`}
                      render={({ field }) => (
                        <FormItem className="space-y-1.5">
                          <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Nombre del Entregable</FormLabel>
                          <FormControl>
                            <Input 
                              placeholder="Ej. Llamadas de Q&A Semanales" 
                              {...field} 
                              className="font-medium bg-background" 
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  {/* Row 2: Metadata Grid */}
                  <div className="grid grid-cols-12 gap-4 items-end">
                    
                    {/* Format (50%) */}
                    <div className="col-span-12 md:col-span-6">
                      <FormField
                        control={form.control}
                        name={`deliverables.${index}.format`}
                        render={({ field }) => (
                          <FormItem className="space-y-1.5">
                            <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Formato de Entrega</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger className="bg-background">
                                  <span className="truncate">
                                    {selectedOption ? selectedOption.label : "Seleccionar formato"}
                                  </span>
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                {formatOptions.map((option) => (
                                  <SelectItem key={option.value} value={option.value} className="py-2">
                                    <div className="flex flex-col gap-0.5">
                                      <span className="font-medium text-sm">{option.label}</span>
                                      {option.description && (
                                        <span className="text-xs text-muted-foreground max-w-[240px] leading-tight">
                                          {option.description}
                                        </span>
                                      )}
                                    </div>
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    {/* Quantity (20%) */}
                    <div className="col-span-6 md:col-span-2">
                      <FormField
                        control={form.control}
                        name={`deliverables.${index}.quantity`}
                        render={({ field }) => (
                          <FormItem className="space-y-1.5">
                            <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Cantidad</FormLabel>
                            <FormControl>
                              <Input 
                                {...field} 
                                className="text-center bg-background" 
                                placeholder="1"
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    {/* Price (20%) */}
                    <div className="col-span-6 md:col-span-3">
                      <FormField
                        control={form.control}
                        name={`deliverables.${index}.value_stack_price`}
                        render={({ field }) => (
                          <FormItem className="space-y-1.5 w-full">
                            <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Valor ($)</FormLabel>
                            <FormControl>
                              <div className="relative">
                                  <span className="absolute left-3 top-2.5 text-xs text-muted-foreground">$</span>
                                  <Input 
                                    type="number" 
                                    placeholder="0"
                                    {...field} 
                                    value={field.value ?? ""}
                                    onChange={e => {
                                      const val = parseFloat(e.target.value);
                                      field.onChange(isNaN(val) ? 0 : val);
                                    }}
                                    className="pl-6 text-right font-mono bg-background"
                                  />
                              </div>
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                    
                    {/* Delete Action (10%) */}
                    <div className="col-span-12 md:col-span-1 flex justify-end md:justify-center pb-0.5">
                      <Button 
                        type="button" 
                        variant="ghost" 
                        size="icon" 
                        onClick={() => remove(index)}
                        className="h-10 w-10 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        title="Eliminar entregable"
                      >
                        <Trash2 className="w-5 h-5" />
                      </Button>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>

          {fields.length === 0 && (
            <div className="flex flex-col items-center justify-center py-10 border-2 border-dashed rounded-lg bg-muted/10 text-muted-foreground">
              <PackageOpen className="w-10 h-10 mb-3 opacity-20" />
              <p className="text-sm font-medium">No hay entregables definidos.</p>
              <p className="text-xs">Agrega items para construir el valor de tu oferta.</p>
              <Button 
                variant="link" 
                onClick={() => append({ name: "", format: DeliverableFormat.RECORDED_CONTENT, quantity: "1", value_stack_price: 0 })}
                className="mt-2 text-primary"
              >
                Agregar el primer item
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
