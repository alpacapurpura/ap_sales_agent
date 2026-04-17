import {
  OfferStatus,
  OfferArchetype,
  OfferValueLevel,
  LEGACY_VALUE_LEVEL_MAP,
  OfferDeliveryModel,
  GuaranteeType,
  DeliverableFormat,
  AssetType,
} from "../types";

import type { Offer, OnboardingMechanism, AccessDuration, PricingStructure } from "../types";
import type { OfferFormValues } from "../types/schema";

// --- Backend DTO types (raw shapes from API) ---

export interface BackendPricing {
  label?: string;
  plan_type?: string;
  total_amount?: number;
  currency?: string;
  deposit_required?: number;
  number_of_installments?: number;
  installment_amount?: number;
  is_default?: boolean;
  savings_claim?: string;
  benefits?: string[];
  is_highlighted?: boolean;
  cta_text?: string;
}

export interface BackendObjection {
  id?: string;
  type?: string;
  trigger_phrases?: string[];
  strategy?: string;
  rebuttal?: string;
}

export interface BackendDeliverable {
  name?: string;
  format?: string;
  quantity?: string | number;
  value_stack_price?: number;
}

export interface BackendAsset {
  id?: string;
  type?: string;
  name?: string;
  url?: string;
  size?: string;
  trigger_context?: string;
  is_knowledge_base?: boolean;
}

// Tipo para la respuesta cruda del backend
export interface BackendOffer {
  id: string;
  name?: string;
  public_name?: string;
  internal_sku?: string;
  archetype: string;
  format_hint?: string;
  is_lead_magnet?: boolean;
  shows_as_lead_magnet?: boolean;
  offer_value_level?: string;
  value_level?: string;
  delivery_model?: string;
  status?: string;
  has_editions?: boolean;

  headline_promise?: string;
  primary_outcome?: string;
  time_to_value?: string;

  pricing?: BackendPricing[];
  pricing_options?: BackendPricing[];
  currency?: string;

  specific_details?: Record<string, unknown>;
  metadata_info?: Record<string, unknown>;

  avatar_id?: string;
  marketing_pain_points?: string[];
  marketing_desires?: string[];
  objections?: BackendObjection[];

  deliverables?: BackendDeliverable[];
  target_avatar_match?: string[];
  prerequisites?: (string | Record<string, unknown>)[];
  includes_offers?: string[];
  assets?: BackendAsset[];

  guarantee_type?: string;
  guarantee_terms?: string;
  access_duration?: string;
  access_duration_text?: string;
  support_duration_days?: number;
  instructors?: string[];

  landing_page_config?: Record<string, unknown>;

  archived_at?: string | null;

  // Campos aplanados que a veces vienen directos
  onboarding_action?: string;
  onboarding_url?: string;
  calendar_type_id?: string;
  checkout_page_url?: string;
  vsl_link?: string;

  [key: string]: unknown;
}

// Helper to normalize enum values
const normalizeEnum = <T extends string>(
  value: string | null | undefined,
  enumObj: Record<string, T>,
  defaultValue: T,
): T => {
  if (!value) return defaultValue;

  // 1. Direct match
  const enumValues = Object.values(enumObj);
  if (enumValues.includes(value as T)) {
    return value as T;
  }

  // 2. Case-insensitive match
  const stringValue = String(value).toUpperCase();
  const match = enumValues.find((v) => String(v).toUpperCase() === stringValue);

  if (match) return match;

  console.warn(`[Adapter] Unknown enum value: ${value}. Defaulting to ${defaultValue}`);
  return defaultValue;
};

/** Normalize value_level with legacy fallback.
 *
 * Paid offers default to ACTIVACION (first paid rung). Only fall back to
 * LEAD_MAGNET when the backend explicitly flags the offer as such — a
 * NULL/missing value_level used to collapse every offer into the lead
 * magnet bucket in Offer Studio, which is the bug this normalizer guards
 * against. See `OfferService._normalize_ladder_position` (backend).
 */
const normalizeLegacyValueLevel = (
  value: string | null | undefined,
  isLeadMagnet: boolean,
): OfferValueLevel => {
  const fallback = isLeadMagnet ? OfferValueLevel.LEAD_MAGNET : OfferValueLevel.ACTIVACION;
  if (!value) return fallback;
  // Direct match with new values
  if (Object.values(OfferValueLevel).includes(value as OfferValueLevel)) {
    return value as OfferValueLevel;
  }
  // Legacy mapping
  const mapped = LEGACY_VALUE_LEVEL_MAP[value];
  if (mapped) return mapped;
  console.warn(`[Adapter] Unknown value_level: ${value}. Defaulting to ${fallback}`);
  return fallback;
};

/**
 * Convierte la respuesta del backend al modelo de dominio Offer del frontend.
 * Maneja la normalización de campos, valores por defecto y extracción de metadata.
 */
export const backendToFrontend = (data: BackendOffer): Offer => {
  const metadata = data.metadata_info || {};

  return {
    id: data.id,
    name: data.name || data.public_name || "Oferta sin nombre",
    internal_sku: data.internal_sku,

    // Strict Enum Normalization
    archetype: normalizeEnum(data.archetype, OfferArchetype, OfferArchetype.PRODUCTO),
    value_level: normalizeLegacyValueLevel(
      data.offer_value_level || data.value_level,
      data.is_lead_magnet || false,
    ),
    delivery_model: normalizeEnum(data.delivery_model, OfferDeliveryModel, OfferDeliveryModel.DIY),
    status: normalizeEnum(data.status, OfferStatus, OfferStatus.DRAFT),
    format_hint: data.format_hint,
    is_lead_magnet: data.is_lead_magnet || false,
    shows_as_lead_magnet: data.shows_as_lead_magnet || false,

    headline_promise: data.headline_promise,
    primary_outcome: data.primary_outcome,
    time_to_value: data.time_to_value,

    pricing: (data.pricing_options || data.pricing || []).map((p: BackendPricing) => ({
      label: p.label || "Standard",
      total_amount: Number(p.total_amount) || 0,
      plan_type: p.plan_type,
      // Pass-through: let UI resolve fallback via useTenantLocale()
      currency: p.currency || data.currency || undefined,
      deposit_required: Number(p.deposit_required) || 0,
      number_of_installments: Number(p.number_of_installments) || 1,
      installment_amount: Number(p.installment_amount) || 0,
    })) as PricingStructure[],
    // Pass-through: let UI resolve fallback via useTenantLocale()
    currency: data.currency || undefined,

    specific_details: data.specific_details || {},
    metadata_info: metadata,
    avatar_id: data.avatar_id,

    marketing_pain_points: data.marketing_pain_points || [],
    marketing_desires: data.marketing_desires || [],
    objections: (data.objections || []).map((o: BackendObjection) => ({
      id: o.id,
      type: o.type || "custom",
      trigger_phrases: o.trigger_phrases || [],
      strategy: o.strategy || "",
      rebuttal: o.rebuttal || "",
    })),
    deliverables: (data.deliverables || []).map((d: BackendDeliverable) => ({
      name: d.name ?? "",
      format: d.format || DeliverableFormat.VIDEO,
      quantity: String(d.quantity || "1"),
      value_stack_price: Number(d.value_stack_price) || 0,
    })),
    target_avatar_match: data.target_avatar_match || [],
    prerequisites: data.prerequisites || [],
    includes_offers: data.includes_offers || [],
    assets: (data.assets || []).map((a: BackendAsset) => ({
      id: a.id,
      type: (a.type as AssetType) || AssetType.URL,
      name: a.name ?? "",
      url: a.url ?? "",
      size: a.size,
      trigger_context: a.trigger_context,
      is_knowledge_base: a.is_knowledge_base,
    })),

    guarantee_type: (data.guarantee_type as GuaranteeType) || GuaranteeType.NONE,
    guarantee_terms: data.guarantee_terms,

    // Prioridad: metadata -> campo directo
    access_duration: ((metadata.access_duration as string | undefined) ||
      data.access_duration) as AccessDuration,
    access_duration_text:
      (metadata.access_duration_text as string | undefined) || data.access_duration_text,
    support_duration_days:
      (metadata.support_duration_days as number | undefined) || data.support_duration_days,

    instructors: data.instructors || [],

    // Prioridad: metadata -> campo directo
    onboarding_action: ((metadata.onboarding_action as string | undefined) ||
      data.onboarding_action) as OnboardingMechanism,
    onboarding_url: (metadata.onboarding_url as string | undefined) || data.onboarding_url,
    calendar_type_id: (metadata.calendar_type_id as string | undefined) || data.calendar_type_id,
    checkout_page_url: (metadata.checkout_page_url as string | undefined) || data.checkout_page_url,
    vsl_link: (metadata.vsl_link as string | undefined) || data.vsl_link,

    landing_page_config: data.landing_page_config as Offer["landing_page_config"],

    // Edition-supporting flag — drives the Offer Studio rail visibility.
    // Backend defaults to `true` for programa/servicio/experiencia and
    // `false` for producto/membresia; we preserve `undefined` only when
    // the backend truly didn't include the field (shouldn't happen post
    // Phase 2, but the rail gracefully hides if so).
    has_editions: data.has_editions,

    archived_at: data.archived_at ?? null,
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
export const frontendToBackend = (
  values: OfferFormValues | Partial<OfferFormValues>,
): Record<string, unknown> => {
  const { pricing_options, ...rest } = values;
  const payload: Record<string, unknown> = { ...rest };

  // Map public_name -> name (ProductCreate expects 'name')
  if (values.public_name && !payload.name) {
    payload.name = values.public_name;
  }

  // pricing_options -> pricing
  if (pricing_options) {
    payload.pricing = pricing_options;
  } else if ("pricing" in values && values.pricing) {
    payload.pricing = values.pricing;
  }

  delete payload.metadata_info;

  return payload;
};
