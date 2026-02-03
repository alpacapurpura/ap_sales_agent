export enum OfferType {
  DIGITAL_PRODUCT = "DIGITAL_PRODUCT",
  COHORT_PROGRAM = "COHORT_PROGRAM",
  HYBRID_MENTORSHIP = "HYBRID_MENTORSHIP",
  SERVICE_RETAINER = "SERVICE_RETAINER",
  CONSULTING_PACKAGE = "CONSULTING_PACKAGE",
  MEMBERSHIP_SUBSCRIPTION = "MEMBERSHIP_SUBSCRIPTION",
}

export enum DeliveryModel {
  DIY = "DIY",
  DWY = "DWY",
  DFY = "DFY",
}

export enum GuaranteeType {
  UNCONDITIONAL_30_DAY = "UNCONDITIONAL_30_DAY",
  CONDITIONAL_ACTION_BASED = "CONDITIONAL_ACTION_BASED",
  PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE",
  NO_REFUNDS = "NO_REFUNDS",
}

export enum DeliverableFormat {
  LIVE_CALL = "LIVE_CALL",
  RECORDED_CONTENT = "RECORDED_CONTENT",
  PDF = "PDF",
  ONE_ON_ONE_CALL = "1ON1_CALL",
}

// --- NEW SPECIFIC ENUMS ---

export enum ProductFormat {
  DIGITAL_DOWNLOAD = "DIGITAL_DOWNLOAD",
  PHYSICAL_GOODS = "PHYSICAL_GOODS",
  HYBRID = "HYBRID",
}

export enum ServiceCapacity {
  OPEN = "OPEN",
  WAITLIST = "WAITLIST",
  CLOSED = "CLOSED",
}

export enum ProgramType {
  EVERGREEN = "EVERGREEN",
  COHORT_BASED = "COHORT_BASED",
  ONE_ON_ONE = "ONE_ON_ONE",
}

export enum BillingFrequency {
  MONTHLY = "MONTHLY",
  QUARTERLY = "QUARTERLY",
  YEARLY = "YEARLY",
}

// --- SHARED INTERFACES ---

export interface PricingStructure {
  label: string;
  total_amount: number;
  deposit_required: number;
  number_of_installments: number;
  installment_amount: number;
  is_default: boolean;
  savings_claim?: string;
}

export interface DeliverableItem {
  name: string;
  format: DeliverableFormat;
  quantity: string;
  value_stack_price: number;
}

// --- SPECIFIC DETAILS INTERFACES ---

export interface ProductDetails {
  format: ProductFormat;
  is_bundle: boolean;
  file_type?: string;
  access_link?: string;
  download_limit?: number;
  stock_quantity: number;
  shipping_zones: string[];
  shipping_cost: number;
  estimated_delivery_days: string;
  bulk_discount_threshold?: number;
}

export interface ServiceDetails {
  capacity_status: ServiceCapacity;
  max_concurrent_clients: number;
  current_active_clients: number;
  deliverables_list: string[];
  excluded_services: string[];
  onboarding_timeline: string;
  min_contract_months: number;
  account_manager_assigned: boolean;
  communication_channels: string[];
}

export interface ProgramDetails {
  program_type: ProgramType;
  duration_weeks: number;
  syllabus_modules: Record<number, string>; // {1: "Module 1"}
  calls_per_week: number;
  call_schedule_details: string;
  are_calls_recorded: boolean;
  one_on_one_sessions: number;
  start_date?: string;
  enrollment_deadline?: string;
  includes_certification: boolean;
  requirements_to_graduate: string;
}

export interface SubscriptionDetails {
  billing_cycle: BillingFrequency;
  trial_period_days: number;
  tier_name: string;
  platform_name: string;
  cancellation_policy: string;
  save_offer_script: string;
  content_update_freq: string;
  expert_guests: boolean;
  networking_events: boolean;
}

export interface Offer {
  id?: string;
  internal_sku: string;
  public_name: string;
  type: OfferType;
  delivery_model: DeliveryModel;
  
  headline_promise: string;
  target_avatar_match: string[]; 
  primary_outcome: string;
  time_to_value: string;
  
  requires_application: boolean;
  min_financial_capacity: string;
  prerequisites: string[];
  
  pricing_options: PricingStructure[];
  currency: string;
  
  guarantee_type: GuaranteeType;
  guarantee_terms: string;
  
  downsell_offer_id?: string;
  upsell_offer_id?: string;
  includes_offers: string[];
  deliverables: DeliverableItem[];
  
  vsl_link?: string;
  checkout_page_url?: string;
  calendar_type_id?: string;
  
  status: string;
  
  // POLYMORPHIC FIELD
  specific_details?: ProductDetails | ServiceDetails | ProgramDetails | SubscriptionDetails;
}
