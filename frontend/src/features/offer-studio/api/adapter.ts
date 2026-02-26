import {
  Offer,
  OfferStatus,
  OfferType,
  OfferValueLevel,
  OfferDeliveryModel,
  GuaranteeType,
  OnboardingMechanism,
  AccessDuration,
  DeliverableFormat,
  PricingStructure
} from "../types";
import { OfferFormValues } from "../types/schema";

// Tipo para la respuesta cruda del backend
export interface BackendOffer {
  id: string;
  name: string;
  public_name?: string;
  internal_sku?: string;
  type: string;
  offer_value_level?: string;
  value_level?: string;
  delivery_model?: string;
  status?: string;
  
  headline_promise?: string;
  primary_outcome?: string;
  time_to_value?: string;
  
  pricing?: any[];
  pricing_options?: any[];
  currency?: string;
  
  specific_details?: Record<string, any>;
  metadata_info?: Record<string, any>;
  
  avatar_id?: string;
  marketing_pain_points?: string[];
  marketing_desires?: string[];
  
  deliverables?: any[];
  target_avatar_match?: string[];
  prerequisites?: any[];
  includes_offers?: string[];
  assets?: any[];

  guarantee_type?: string;
  guarantee_terms?: string;
  access_duration?: string;
  access_duration_text?: string;
  support_duration_days?: number;
  instructors?: string[];
  
  landing_page_config?: any;

  // Campos aplanados que a veces vienen directos
  onboarding_action?: string;
  onboarding_url?: string;
  calendar_type_id?: string;
  checkout_page_url?: string;
  vsl_link?: string;
  
  [key: string]: any;
}

/**
 * Convierte la respuesta del backend al modelo de dominio Offer del frontend.
 * Maneja la normalización de campos, valores por defecto y extracción de metadata.
 */
export const backendToFrontend = (data: BackendOffer): Offer => {
  const metadata = data.metadata_info || {};

  return {
    id: data.id,
    name: data.name,
    internal_sku: data.internal_sku,
    type: (data.type?.toUpperCase() as OfferType) || OfferType.FREE_RESOURCE,
    
    value_level: (data.offer_value_level || data.value_level || "N0") as OfferValueLevel,
    delivery_model: (data.delivery_model || "DIY") as OfferDeliveryModel,
    status: (data.status?.toUpperCase() || "DRAFT") as OfferStatus,
    
    headline_promise: data.headline_promise,
    primary_outcome: data.primary_outcome,
    time_to_value: data.time_to_value,
    
    pricing: (data.pricing_options || data.pricing || []).map((p: any) => ({
        label: p.label || "Standard",
        total_amount: Number(p.total_amount) || 0,
        plan_type: p.plan_type,
        currency: p.currency || data.currency || "USD",
        deposit_required: Number(p.deposit_required) || 0,
        number_of_installments: Number(p.number_of_installments) || 1,
        installment_amount: Number(p.installment_amount) || 0
    })) as PricingStructure[],
    currency: data.currency || "USD",
    
    specific_details: data.specific_details || {},
    metadata_info: metadata,
    avatar_id: data.avatar_id,

    marketing_pain_points: data.marketing_pain_points || [],
    marketing_desires: data.marketing_desires || [],
    deliverables: (data.deliverables || []).map((d: any) => ({
        name: d.name,
        format: d.format || DeliverableFormat.RECORDED_CONTENT,
        quantity: String(d.quantity || "1"),
        value_stack_price: Number(d.value_stack_price) || 0
    })),
    target_avatar_match: data.target_avatar_match || [],
    prerequisites: data.prerequisites || [],
    includes_offers: data.includes_offers || [],
    assets: data.assets || [],

    guarantee_type: (data.guarantee_type as GuaranteeType) || GuaranteeType.NO_REFUNDS,
    guarantee_terms: data.guarantee_terms,
    
    // Prioridad: metadata -> campo directo
    access_duration: (metadata.access_duration || data.access_duration) as AccessDuration,
    access_duration_text: metadata.access_duration_text || data.access_duration_text,
    support_duration_days: metadata.support_duration_days || data.support_duration_days,
    
    instructors: data.instructors || [],
    
    // Prioridad: metadata -> campo directo
    onboarding_action: (metadata.onboarding_action || data.onboarding_action) as OnboardingMechanism,
    onboarding_url: metadata.onboarding_url || data.onboarding_url,
    calendar_type_id: metadata.calendar_type_id || data.calendar_type_id,
    checkout_page_url: metadata.checkout_page_url || data.checkout_page_url,
    vsl_link: metadata.vsl_link || data.vsl_link,

    landing_page_config: data.landing_page_config
  };
};

/**
 * Convierte un objeto Offer (dominio) a OfferFormValues (formulario).
 * Útil para inicializar el formulario en DynamicOfferEditor.
 */
export const offerToFormValues = (offer: Offer): OfferFormValues => {
    return {
        ...offer,
        public_name: offer.name,
        pricing_options: offer.pricing || [],
        // Aseguramos que los campos opcionales no sean undefined si el schema lo requiere
        // aunque OfferFormValues usa partials/optionals mayormente.
    } as unknown as OfferFormValues;
};

/**
 * Convierte los valores del formulario al payload que espera el backend.
 */
export const frontendToBackend = (values: OfferFormValues | Partial<OfferFormValues>): Record<string, any> => {
    const payload: Record<string, any> = { ...values };
    
    // 1. Mapear pricing_options (Frontend) -> pricing_options (Backend)
    // El backend espera 'pricing_options', no 'pricing'
    if (values.pricing_options) {
        payload.pricing_options = values.pricing_options;
    } else if (values.pricing) {
        payload.pricing_options = values.pricing;
        delete payload.pricing;
    }
    
    // 2. Eliminar metadata_info para evitar sobrescribir actualizaciones parciales
    // El backend maneja la fusión de campos específicos en metadata si es necesario.
    delete payload.metadata_info;
    
    // 3. Mapear public_name
    // Si existe public_name, se usa. Si no, y existe name, se usa name como public_name.
    if (values.public_name) {
        payload.public_name = values.public_name;
    } else if (values.name) {
        payload.public_name = values.name;
    }

    return payload;
};
