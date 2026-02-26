export enum LifecycleStage {
  LEAD = 'lead',
  ONBOARDING = 'onboarding',
  ACTIVE = 'active',
  AT_RISK = 'at_risk',
  CHURNED = 'churned',
}

export interface RFMData {
  recency: number; // Days since last purchase
  frequency: number; // Number of purchases
  monetary: number; // Total spent
  score: number; // Calculated score (1-5 or similar)
  segment: string; // e.g., "Champions", "Loyal Customers", "At Risk"
}

export interface CustomerProfile {
  id: string;
  name: string;
  email: string;
  phone?: string;
  lifecycleStage: LifecycleStage;
  rfm: RFMData;
  lastInteraction: string; // ISO date string
  ltv: number; // Lifetime Value
  tags: string[];
}

export interface JourneyEvent {
  id: string;
  profileId: string;
  eventType: 'email_open' | 'click' | 'purchase' | 'page_view' | 'support_ticket';
  timestamp: string; // ISO date string
  description: string;
  channel: 'email' | 'web' | 'sms' | 'whatsapp';
  metadata?: Record<string, any>;
}
