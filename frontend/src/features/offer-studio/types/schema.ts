import { z } from "zod";
import { 
  DeliveryModel, GuaranteeType, OfferType, DeliverableFormat,
  ProductFormat, ServiceCapacity, ProgramType, BillingFrequency
} from "./index";

export const PricingStructureSchema = z.object({
  label: z.string().min(1, "Label is required"),
  total_amount: z.number().min(0),
  deposit_required: z.number().min(0).default(0),
  number_of_installments: z.number().int().min(1).default(1),
  installment_amount: z.number().min(0).default(0),
  is_default: z.boolean().default(false),
  savings_claim: z.string().optional(),
});

export const DeliverableItemSchema = z.object({
  name: z.string().min(1, "Name is required"),
  format: z.nativeEnum(DeliverableFormat),
  quantity: z.string().min(1),
  value_stack_price: z.number().min(0),
});

// --- POLYMORPHIC DETAILS SCHEMAS ---

export const ProductDetailsSchema = z.object({
  format: z.nativeEnum(ProductFormat),
  is_bundle: z.boolean().default(false),
  file_type: z.string().optional(),
  access_link: z.string().url().optional(),
  download_limit: z.number().optional(),
  stock_quantity: z.number().int().default(0),
  shipping_zones: z.array(z.string()).default([]),
  shipping_cost: z.number().min(0).default(0),
  estimated_delivery_days: z.string().default("3-5 días hábiles"),
  bulk_discount_threshold: z.number().int().optional(),
});

export const ServiceDetailsSchema = z.object({
  capacity_status: z.nativeEnum(ServiceCapacity),
  max_concurrent_clients: z.number().int().min(1),
  current_active_clients: z.number().int().default(0),
  deliverables_list: z.array(z.string()).min(1),
  excluded_services: z.array(z.string()).default([]),
  onboarding_timeline: z.string().min(1),
  min_contract_months: z.number().int().min(1).default(1),
  account_manager_assigned: z.boolean().default(false),
  communication_channels: z.array(z.string()).default(["Email"]),
});

export const ProgramDetailsSchema = z.object({
  program_type: z.nativeEnum(ProgramType),
  duration_weeks: z.number().int().min(1),
  syllabus_modules: z.record(z.string(), z.string().min(1)).default({}), // z.record keys are always strings in JS
  calls_per_week: z.number().int().min(0),
  call_schedule_details: z.string(),
  are_calls_recorded: z.boolean().default(true),
  one_on_one_sessions: z.number().int().default(0),
  start_date: z.string().optional(),
  enrollment_deadline: z.string().optional(),
  includes_certification: z.boolean().default(false),
  requirements_to_graduate: z.string().optional(),
});

export const SubscriptionDetailsSchema = z.object({
  billing_cycle: z.nativeEnum(BillingFrequency),
  trial_period_days: z.number().int().default(0),
  tier_name: z.string().min(1),
  platform_name: z.string().min(1),
  cancellation_policy: z.string().min(1),
  save_offer_script: z.string().optional(),
  content_update_freq: z.string().min(1),
  expert_guests: z.boolean().default(false),
  networking_events: z.boolean().default(false),
});

export const OfferSchema = z.object({
  internal_sku: z.string().min(1, "SKU is required"),
  public_name: z.string().min(1, "Name is required"),
  type: z.nativeEnum(OfferType),
  delivery_model: z.nativeEnum(DeliveryModel),
  
  headline_promise: z.string().min(10, "Promise must be descriptive"),
  target_avatar_match: z.array(z.string()).default([]),
  primary_outcome: z.string().min(1, "Outcome is required"),
  time_to_value: z.string().min(1, "Time to value is required"),
  
  requires_application: z.boolean().default(false),
  min_financial_capacity: z.string().min(1),
  prerequisites: z.array(z.string()).default([]),
  
  pricing_options: z.array(PricingStructureSchema).min(1, "At least one pricing option is required"),
  currency: z.string().default("USD"),
  
  guarantee_type: z.nativeEnum(GuaranteeType),
  guarantee_terms: z.string().min(10, "Guarantee terms are required"),
  
  downsell_offer_id: z.string().uuid().optional().or(z.literal("")),
  upsell_offer_id: z.string().uuid().optional().or(z.literal("")),
  includes_offers: z.array(z.string().uuid()).default([]),
  deliverables: z.array(DeliverableItemSchema).default([]),
  
  vsl_link: z.string().url().optional().or(z.literal("")),
  checkout_page_url: z.string().url().optional().or(z.literal("")),
  calendar_type_id: z.string().optional(),
  
  status: z.string().default("ACTIVE"),
  
  // Polymorphic Validation is tricky in Zod without superRefine or discriminatedUnion at root
  // For simplicity in form, we'll keep it as optional objects that are validated based on 'type' manually or loosely here
  specific_details: z.union([
    ProductDetailsSchema,
    ServiceDetailsSchema,
    ProgramDetailsSchema,
    SubscriptionDetailsSchema
  ]).optional(),
});

export type OfferFormValues = z.infer<typeof OfferSchema>;
