export type LeadTemperature = 'cold' | 'warm' | 'hot';
export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'proposal' | 'won' | 'lost';

export interface Lead {
  id: string;
  name: string;
  avatarUrl?: string;
  initials?: string;
  role?: string;
  company?: string;
  email?: string;
  phone?: string;
  score: number;
  temperature: LeadTemperature;
  status: LeadStatus;
  lastActivity?: string;
  nextAction?: string;
  tags?: string[];
}
