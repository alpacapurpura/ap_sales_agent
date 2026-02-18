import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { OfferType } from "../../types";
import { ContextualHint } from "../ui/contextual-hint";
import { ProductDetailsForm } from "../forms/product-form";
import { ServiceDetailsForm } from "../forms/service-form";
import { ProgramDetailsForm } from "../forms/program-form";
import { SubscriptionDetailsForm } from "../forms/subscription-form";
import { EventDetailsForm } from "../forms/event-form";

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

  const renderDetailsForm = () => {
    // 1. PRODUCTS (DIY)
    if ([
      OfferType.FREE_RESOURCE, 
      OfferType.TRIPWIRE_OFFER, 
      OfferType.SELF_PACED_COURSE, 
      OfferType.PHYSICAL_MERCH,
      OfferType.CONTENT_ASSET_PODCAST
    ].includes(offerType)) {
      return <ProductDetailsForm form={form} />;
    }

    // 2. PROGRAMS (DWY)
    if ([
      OfferType.HYBRID_MENTORSHIP, 
      OfferType.COHORT_BASED_COURSE, 
      OfferType.GROUP_COACHING_PROGRAM,
      OfferType.FREE_WEBINAR_CHALLENGE
    ].includes(offerType)) {
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
    ].includes(offerType)) {
      return <ServiceDetailsForm form={form} />;
    }

    // 4. SUBSCRIPTIONS
    if ([
      OfferType.PAID_NEWSLETTER_SUBSCRIPTION, 
      OfferType.COMMUNITY_LITE
    ].includes(offerType)) {
      return <SubscriptionDetailsForm form={form} />;
    }

    // 5. EVENTS
    if ([
      OfferType.MASTERMIND_NETWORK, 
      OfferType.LUXURY_RETREAT
    ].includes(offerType)) {
      return <EventDetailsForm form={form} />;
    }

    return (
      <div className="p-8 text-center border-2 border-dashed rounded-lg text-muted-foreground">
        <p>Tipo de oferta no reconocido o sin formulario específico: {offerType}</p>
      </div>
    );
  };

  return (
    <div className="animate-in fade-in-50 duration-500 space-y-6">
      <ContextualHint type={offerType} />
      {renderDetailsForm()}
    </div>
  );
}
