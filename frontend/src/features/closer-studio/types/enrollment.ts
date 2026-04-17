/**
 * Enrollment types mirroring the backend DTOs
 * (`backend/src/modules/sales_agent/api/dto/enrollments.py`).
 */

export enum EnrollmentStatus {
  INTENT = "intent",
  WAITLIST = "waitlist",
  PAYMENT_PENDING = "payment_pending",
  PAID = "paid",
  ATTENDED = "attended",
  REFUNDED = "refunded",
  CANCELLED = "cancelled",
}

export enum PaymentProvider {
  STRIPE = "stripe",
  MERCADOPAGO = "mercadopago",
  CULQI = "culqi",
  MANUAL = "manual",
}

export interface Enrollment {
  id: string;
  tenant_id: string;
  offer_id: string;
  edition_id: string | null;
  contact_id: string;
  conversation_id: string | null;
  status: EnrollmentStatus;
  pricing_tier_label: string | null;
  pricing_amount: number | null;
  currency: string | null;
  payment_provider: PaymentProvider | null;
  payment_transaction_id: string | null;
  payment_link_url: string | null;
  paid_at: string | null;
  source_channel: string | null;
  notes: string | null;
  extra: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
}

export interface EnrollmentListResponse {
  items: Enrollment[];
  total: number;
}

export interface EnrollmentFilters {
  offer_id?: string;
  edition_id?: string;
  status?: EnrollmentStatus;
  contact_id?: string;
}

export interface PromoteWaitlistResponse {
  promoted: number;
  skipped: number;
  items: Enrollment[];
}
