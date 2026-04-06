import React from 'react';
import { Badge } from '@/components/ui/badge';
import { OfferFormValues } from '../../../../types/schema';
import { useFormContext } from 'react-hook-form';
import { CreditCard } from 'lucide-react';
import { formatMoney } from '@/lib/format-money';

interface PricingPreviewProps {
  data?: Partial<OfferFormValues>;
}

export const PricingPreview = ({ data: propsData }: PricingPreviewProps) => {
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);

  if (!data?.pricing_options?.length) return null;

  const { pricing_options, currency } = data;
  const currencyCode = currency || "USD";

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 gap-3">
        {pricing_options.map((option, idx) => (
          <div 
            key={idx} 
            className={`
              relative p-4 rounded-xl border transition-all
              ${option.is_default 
                ? 'border-primary/20 bg-primary/5 shadow-sm' 
                : 'border-border/60 bg-card/50 hover:bg-card'}
            `}
          >
            {option.is_default && (
              <div className="absolute -top-2.5 right-4">
                <Badge variant="default" className="text-[10px] px-2 py-0.5 h-5 font-normal tracking-wide uppercase">
                  Popular
                </Badge>
              </div>
            )}
            
            <div className="flex items-baseline justify-between mb-2">
              <h4 className="font-semibold text-base tracking-tight">{option.label}</h4>
              <div className="text-right">
                 <span className="text-2xl font-bold tracking-tighter">{formatMoney(option.total_amount, currencyCode, { fractionDigits: 0 })}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <CreditCard className="w-3.5 h-3.5" />
              <span>
                {option.number_of_installments > 1 
                  ? `${option.number_of_installments} pagos de ${option.installment_amount}`
                  : "Pago único"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
