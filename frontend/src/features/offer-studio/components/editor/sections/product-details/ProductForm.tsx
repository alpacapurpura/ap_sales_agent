"use client";

import { Card, CardContent } from "@/components/ui/card";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RichSelect } from "@/components/ui/rich-select";
import { Switch } from "@/components/ui/switch";

import { FulfillmentType } from "../../../../types";
import { OfferSchema } from "../../../../types/schema";
import type { OfferFormValues } from "../../../../types/schema";

import { SectionFormWrapper } from "../common/SectionFormWrapper";

import type { UseFormReturn } from "react-hook-form";

import {
  FULFILLMENT_TYPE_METADATA,
  DIGITAL_FORMAT_METADATA,
  getEnumOptions,
} from "../../../../types/enum-metadata";

const ProductDetailsSchema = OfferSchema.pick({
  specific_details: true,
});

type ProductDetailsFormValues = Pick<OfferFormValues, "specific_details">;

export interface ProductDetailsFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: UseFormReturn<OfferFormValues>;
}

function ProductDetailsContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-6">
          <h3 className="text-lg font-medium">Logística del Producto</h3>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="specific_details.fulfillment_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tipo de Entrega</FormLabel>
                  <RichSelect
                    options={getEnumOptions(FULFILLMENT_TYPE_METADATA)}
                    value={field.value as string}
                    onValueChange={field.onChange}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="specific_details.format"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Formato Digital</FormLabel>
                  <RichSelect
                    options={getEnumOptions(DIGITAL_FORMAT_METADATA)}
                    value={field.value as string}
                    onValueChange={field.onChange}
                  />
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="specific_details.access_url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL de Acceso</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="https://..."
                      {...field}
                      value={(field.value as string) || ""}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="specific_details.estimated_consumption_time_minutes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Minutos Estimados</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                      value={(field.value as number) || 0}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {form.watch("specific_details.fulfillment_type") ===
            FulfillmentType.PHYSICAL_SHIPPING && (
            <div className="border p-4 rounded-md space-y-4 bg-muted/20">
              <h4 className="font-medium text-sm text-muted-foreground">Logística Física</h4>
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="specific_details.requires_shipping"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm bg-background">
                      <div className="space-y-0.5">
                        <FormLabel>Requiere Envío</FormLabel>
                      </div>
                      <FormControl>
                        <Switch checked={field.value as boolean} onCheckedChange={field.onChange} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="specific_details.stock_quantity"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Stock</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          {...field}
                          onChange={(e) => field.onChange(parseInt(e.target.value))}
                          value={(field.value as number) || 0}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <FormField
                control={form.control}
                name="specific_details.sku_inventory_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>SKU Interno</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="MERCH-001"
                        {...field}
                        value={(field.value as string) || ""}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function ProductDetailsForm({ defaultValues: propValues, onSave }: ProductDetailsFormProps) {
  const defaultValues: ProductDetailsFormValues = {
    specific_details: propValues?.specific_details || {},
  };

  const handleSave = async (data: ProductDetailsFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<ProductDetailsFormValues>
      schema={ProductDetailsSchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => <ProductDetailsContent form={form as unknown as UseFormReturn<OfferFormValues>} />}
    </SectionFormWrapper>
  );
}
