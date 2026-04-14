"use client";

import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { OfferDeliveryModel as DeliveryModel, OfferArchetype } from "../../../../types";
import { ARCHETYPE_METADATA } from "../../../../config/archetype-metadata";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

// Define partial schema for Identity
const IdentitySchema = OfferSchema.pick({
  public_name: true,
  delivery_model: true,
});

type IdentityFormValues = Pick<OfferFormValues, "public_name" | "delivery_model">;

export interface IdentityFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: UseFormReturn<OfferFormValues>;
}

const DELIVERY_MODEL_DESCRIPTIONS: Record<string, string> = {
  [DeliveryModel.DIY]:
    "Do It Yourself. El cliente implementa la solución por su cuenta con tus recursos.",
  [DeliveryModel.DWY]:
    "Done With You. Colaboración activa entre tú y el cliente para lograr el resultado.",
  [DeliveryModel.DFY]:
    "Done For You. Tú o tu equipo ejecutan todo el trabajo operativo por el cliente.",
  [DeliveryModel.HYBRID]:
    "Híbrido / B2B. Soluciones corporativas o modelos mixtos diseñados para empresas.",
};

function IdentityContent({
  form,
  archetype,
}: {
  form: UseFormReturn<OfferFormValues>;
  archetype?: string;
}) {
  const archetypeMeta = archetype ? ARCHETYPE_METADATA[archetype as OfferArchetype] : null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1">
        <FormField
          control={form.control}
          name="public_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre Público</FormLabel>
              <WithCopilot
                fieldId="public_name"
                fieldLabel="Nombre Público"
                getValue={() => field.value || ""}
              >
                <FormControl>
                  <Input placeholder="Agency Accelerator 3.0" {...field} />
                </FormControl>
              </WithCopilot>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card className="bg-background">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Archetype</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2">
              <Badge variant="outline" className="w-fit">
                {archetypeMeta?.label || archetype || "No definido"}
              </Badge>
              <p className="text-sm text-muted-foreground">
                {archetypeMeta?.subtitle || "Descripción no disponible."}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-background">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Modelo de Entrega
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2">
              <Badge variant="outline" className="w-fit">
                {form.watch("delivery_model") || "N/A"}
              </Badge>
              <p className="text-sm text-muted-foreground">
                {DELIVERY_MODEL_DESCRIPTIONS[form.watch("delivery_model") || ""] ||
                  "Descripción no disponible."}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function IdentityForm({ defaultValues: propValues, onSave }: IdentityFormProps) {
  const defaultValues: IdentityFormValues = {
    public_name: propValues?.public_name || "",
    delivery_model: propValues?.delivery_model || DeliveryModel.DWY,
  };

  const handleSave = async (data: IdentityFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<IdentityFormValues>
      schema={IdentitySchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <IdentityContent
          form={form as unknown as UseFormReturn<OfferFormValues>}
          archetype={propValues?.archetype as string}
        />
      )}
    </SectionFormWrapper>
  );
}
