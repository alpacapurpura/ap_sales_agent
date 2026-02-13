import { UseFormReturn } from "react-hook-form";
import { OfferFormValues, OfferType } from "../../types/schema";
import { PolymorphicFactory } from "../ui/polymorphic-factory";
import { ContextualHint } from "../ui/contextual-hint";

interface StepProps {
  form: UseFormReturn<OfferFormValues>;
}

export function SpecificDetailsStep({ form }: StepProps) {
  const offerType = form.watch("type");

  if (!offerType) {
    return (
      <div className="text-center p-8 text-muted-foreground border-2 border-dashed rounded-lg">
        <p>Selecciona un Tipo de Oferta en el paso &quot;Identidad&quot; para ver los campos específicos.</p>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in-50 duration-500 space-y-6">
      <ContextualHint type={offerType} />
      <PolymorphicFactory type={offerType} form={form} />
    </div>
  );
}
