export interface Customer {
  id: string;
  full_name: string;
  email?: string;
  phone?: string;
  avatar_url?: string;
  social_handle?: string;
}

export type LeadStatus = "new" | "contacted" | "qualified" | "proposal" | "won" | "lost";
export type LeadTemperature = "cold" | "warm" | "hot";

export interface Lead {
  id: string;
  status: LeadStatus;
  temperature: LeadTemperature;
  score: number;
  ai_memory?: string; // Memory or notes from AI interaction
  customer: Customer;
}
