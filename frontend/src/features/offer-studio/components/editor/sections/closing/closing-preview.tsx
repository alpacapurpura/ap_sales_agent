import React from 'react';
import { OfferFormValues } from '../../../../types/schema';
import { useFormContext } from 'react-hook-form';
import { ShieldCheck } from 'lucide-react';
import { GuaranteeType } from '../../../../types';

interface ClosingPreviewProps {
  data?: Partial<OfferFormValues>;
}

const GUARANTEE_LABELS: Record<string, string> = {
    [GuaranteeType.NO_REFUNDS]: "Sin Reembolsos",
    [GuaranteeType.UNCONDITIONAL_X_DAY]: "Garantía Incondicional",
    [GuaranteeType.CONDITIONAL_ACTION_BASED]: "Garantía Condicional",
    [GuaranteeType.EXCHANGE_ONLY]: "Solo Intercambio"
};

export const ClosingPreview = ({ data: propsData }: ClosingPreviewProps) => {
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);

  if (!data) return null;

  const { guarantee_type, guarantee_terms } = data;

  if (guarantee_type === GuaranteeType.NO_REFUNDS && !guarantee_terms) {
      return null;
  }

  return (
    <div className="w-full flex flex-col items-center justify-center text-center p-6 rounded-2xl bg-gradient-to-b from-muted/30 to-muted/10 border border-muted/50">
      <div className="mb-3 p-3 rounded-full bg-background shadow-sm ring-1 ring-border/50">
        <ShieldCheck className="w-8 h-8 text-primary" strokeWidth={1.5} />
      </div>
      
      <h4 className="text-base font-bold tracking-tight text-foreground mb-1">
        {GUARANTEE_LABELS[guarantee_type || GuaranteeType.NO_REFUNDS] || guarantee_type}
      </h4>
      
      <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold mb-3">
        Garantía Oficial
      </p>

      {guarantee_terms && (
        <div className="text-xs text-muted-foreground/80 max-w-xs leading-relaxed">
           &quot;{guarantee_terms}&quot;
        </div>
      )}
    </div>
  );
};
