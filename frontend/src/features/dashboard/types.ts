export interface DashboardMetrics {
  pipeline_value: number;
  active_leads_count: number;
  conversion_rate: number;
}

export interface ActionItem {
  id: string;
  type: 'INTERVENTION' | 'GAP' | 'BOOKING' | 'ALERT';
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description: string;
  link?: string;
  timestamp: string;
}

export interface AgendaItem {
  id: string;
  title: string;
  start_time: string;
  attendee_name: string;
  status: string;
}

export interface FunnelStage {
  stage: string;
  count: number;
  value: number;
}

export interface DashboardResponse {
  metrics: DashboardMetrics;
  action_items: ActionItem[];
  agenda: AgendaItem[];
  funnel: FunnelStage[];
}
