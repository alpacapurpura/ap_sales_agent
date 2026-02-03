import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { OfferType, ProductFormat, ServiceCapacity, ProgramType, BillingFrequency } from "../../types/index";
import { ProductDetailsForm } from "../forms/product-form";
import { ServiceDetailsForm } from "../forms/service-form";
import { ProgramDetailsForm } from "../forms/program-form";
import { SubscriptionDetailsForm } from "../forms/subscription-form";

interface StepProps {
  form: any; // We use 'any' temporarily to avoid deep typing issues with the polymorphic sub-forms, but schemas are strict
}

export function SpecificDetailsStep({ form }: StepProps) {
  const offerType = form.watch("type");

  if (offerType === OfferType.DIGITAL_PRODUCT || offerType === "PHYSICAL_GOODS" as any) {
    return <ProductDetailsForm form={form} />;
  }

  if (offerType === OfferType.SERVICE_RETAINER || offerType === OfferType.CONSULTING_PACKAGE) {
    return <ServiceDetailsForm form={form} />;
  }

  if (offerType === OfferType.COHORT_PROGRAM || offerType === OfferType.HYBRID_MENTORSHIP) {
    return <ProgramDetailsForm form={form} />;
  }

  if (offerType === OfferType.MEMBERSHIP_SUBSCRIPTION) {
    return <SubscriptionDetailsForm form={form} />;
  }

  return (
    <div className="text-center p-8 text-muted-foreground border-2 border-dashed rounded-lg">
      <p>Selecciona un Tipo de Oferta en el paso &quot;Identidad&quot; para ver los campos específicos.</p>
      <p className="text-xs mt-2">Tipo actual: {offerType || "Ninguno"}</p>
    </div>
  );
}
