export type StrategyStage = 
  | 'UNIVERSE' 
  | 'ACQUISITION' 
  | 'ACTIVATION' 
  | 'NUTRITION' 
  | 'CONVERSION' 
  | 'ADOPTION' 
  | 'EXPANSION' 
  | 'EVANGELIZATION';

export type ChannelType = 
  | 'PAID_MEDIA' 
  | 'ORGANIC_SEARCH' 
  | 'ORGANIC_SOCIAL' 
  | 'OWNED_MEDIA' 
  | 'SALES_TEAM' 
  | 'PARTNERS';

export type ActionStatus = 
  | 'POTENTIAL'   // Gray, Dotted
  | 'HEALTHY'     // Solid, Colored
  | 'BOTTLENECK'; // Red, Pulsing

export type FinancialNature = 
  | 'EXPENSE' 
  | 'REVENUE' 
  | 'NEUTRAL';

export interface NodeMetric {
  value: number;
  label: string;
  unit?: string; // '$', '%', etc.
  trend?: 'up' | 'down' | 'neutral';
}

export interface MarketingNode {
  id: string;
  stage: StrategyStage;
  title: string;
  description: string;
  volumeMetric: NodeMetric;
  efficiencyMetric: NodeMetric;
  financialMetric?: NodeMetric; // For Conversion stage and onwards
  order: number; // 0 to 7
}

export interface MarketingActionLink {
  source: string; // Node ID
  target: string; // Node ID
  value: number; // Volume/Thickness
  channelType: ChannelType;
  status: ActionStatus;
  financialNature: FinancialNature;
  label: string; // Campaign Name
  metadata?: {
    cost?: number;
    revenue?: number;
    ctr?: number;
    cpa?: number;
    [key: string]: any;
  };
}

export interface StrategyCanvasConfig {
  nodes: MarketingNode[];
  links: MarketingActionLink[];
}
