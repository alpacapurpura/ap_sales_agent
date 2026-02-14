import { OfferType } from "../../types/schema";
import { ProductDetailsForm } from "../forms/product-form";
import { ServiceDetailsForm } from "../forms/service-form";
import { ProgramDetailsForm } from "../forms/program-form";
import { SubscriptionDetailsForm } from "../forms/subscription-form";
import { EventDetailsForm } from "../forms/event-form";
import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";

interface PolymorphicFactoryProps {
  type: OfferType;
  form: UseFormReturn<OfferFormValues>;
}

export function PolymorphicFactory({ type, form }: PolymorphicFactoryProps) {
  // Mapping logic based on OFFER_TYPE_TO_DETAILS_MAPPING (Backend)
  
  // 1. PRODUCTS (DIY)
  if ([
    OfferType.FREE_RESOURCE, 
    OfferType.TRIPWIRE_OFFER, 
    OfferType.SELF_PACED_COURSE, 
    OfferType.PHYSICAL_MERCH,
    OfferType.CONTENT_ASSET_PODCAST
  ].includes(type)) {
    return <ProductDetailsForm form={form} />;
  }

  // 2. PROGRAMS (DWY)
  if ([
    OfferType.HYBRID_MENTORSHIP, 
    OfferType.COHORT_BASED_COURSE, 
    OfferType.GROUP_COACHING_PROGRAM,
    OfferType.FREE_WEBINAR_CHALLENGE
  ].includes(type)) {
    return <ProgramDetailsForm form={form} />;
  }

  // 3. SERVICES (Advisory/Agency)
  if ([
    OfferType.VIP_DAY_STRATEGY, 
    OfferType.ONE_ON_ONE_PRIVATE_MENTORING, 
    OfferType.DEEP_DIVE_AUDIT, 
    OfferType.PRODUCTIZED_SERVICE, 
    OfferType.MONTHLY_RETAINER,
    OfferType.PERFORMANCE_REV_SHARE,
    OfferType.CORPORATE_TRAINING,
    OfferType.BRAND_SPONSORSHIP,
    OfferType.KEYNOTE_SPEAKING
  ].includes(type)) {
    // Exception: If it's a Retainer, it might be ServiceDetails in backend.
    // Checking schema.py: MONTHLY_RETAINER -> ServiceDetails. Correct.
    return <ServiceDetailsForm form={form} />;
  }

  // 4. SUBSCRIPTIONS
  if ([
    OfferType.PAID_NEWSLETTER_SUBSCRIPTION, 
    OfferType.COMMUNITY_LITE
  ].includes(type)) {
    return <SubscriptionDetailsForm form={form} />;
  }

  // 5. EVENTS
  if ([
    OfferType.MASTERMIND_NETWORK, 
    OfferType.LUXURY_RETREAT
  ].includes(type)) {
    return <EventDetailsForm form={form} />;
  }

  return (
    <div className="p-8 text-center border-2 border-dashed rounded-lg text-muted-foreground">
      <p>Tipo de oferta no reconocido o sin formulario específico: {type}</p>
    </div>
  );
}
