'use client';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import type { OfferSaleData } from '../../../types/metrics';
import { OfferCard } from './OfferCard';

interface TierGroupProps {
  tierKey: string;
  tierLabel: string;
  offers: OfferSaleData[];
  defaultOpen?: boolean;
}

export function TierGroup({ tierKey, tierLabel, offers, defaultOpen }: TierGroupProps) {
  const shouldOpen = defaultOpen ?? offers.some((o) => o.salesCount > 0);

  return (
    <Accordion type="single" collapsible defaultValue={shouldOpen ? tierKey : undefined}>
      <AccordionItem value={tierKey} className="border-none">
        <AccordionTrigger className="py-2 px-3 hover:no-underline">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {tierLabel}
          </span>
        </AccordionTrigger>
        <AccordionContent>
          <div className="space-y-2">
            {offers.map((offer) => (
              <OfferCard key={offer.offerId} offer={offer} tierKey={tierKey} />
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
