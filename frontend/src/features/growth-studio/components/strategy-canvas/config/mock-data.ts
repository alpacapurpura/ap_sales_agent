import type { StrategyCanvasConfig, MarketingNode, MarketingActionLink } from "./types";

export const STRATEGY_NODES: MarketingNode[] = [
  {
    id: "node-0",
    stage: "UNIVERSE",
    title: "Universo",
    description: "Total Addressable Market",
    order: 0,
    volumeMetric: { label: "Impresiones", value: 1500000 },
    efficiencyMetric: { label: "CPM", value: 2.5, unit: "$" },
  },
  {
    id: "node-1",
    stage: "ACQUISITION",
    title: "Adquisición",
    description: "Visitantes Web/Perfil",
    order: 1,
    volumeMetric: { label: "Visitas", value: 45000 },
    efficiencyMetric: { label: "CPC", value: 0.85, unit: "$" },
  },
  {
    id: "node-2",
    stage: "ACTIVATION",
    title: "Activación",
    description: "Leads Capturados",
    order: 2,
    volumeMetric: { label: "Leads", value: 8500 },
    efficiencyMetric: { label: "CPL", value: 4.5, unit: "$" },
  },
  {
    id: "node-3",
    stage: "NUTRITION",
    title: "Nutrición",
    description: "MQLs Listos",
    order: 3,
    volumeMetric: { label: "MQLs", value: 3200 },
    efficiencyMetric: { label: "Engagement", value: 45, unit: "%" },
  },
  {
    id: "node-4",
    stage: "CONVERSION",
    title: "Conversión",
    description: "Nuevos Clientes",
    order: 4,
    volumeMetric: { label: "Ventas", value: 450 },
    efficiencyMetric: { label: "CAC", value: 35.0, unit: "$" },
    financialMetric: { label: "Revenue", value: 45000, unit: "$" },
  },
  {
    id: "node-5",
    stage: "ADOPTION",
    title: "Adopción",
    description: "Usuarios Activos",
    order: 5,
    volumeMetric: { label: "Activos", value: 400 },
    efficiencyMetric: { label: "Time-to-Value", value: 2, unit: "días" },
  },
  {
    id: "node-6",
    stage: "EXPANSION",
    title: "Expansión",
    description: "Upsells / Cross-sells",
    order: 6,
    volumeMetric: { label: "Recurrentes", value: 120 },
    efficiencyMetric: { label: "LTV", value: 850, unit: "$" },
  },
  {
    id: "node-7",
    stage: "EVANGELIZATION",
    title: "Evangelización",
    description: "Referidos",
    order: 7,
    volumeMetric: { label: "Referidos", value: 35 },
    efficiencyMetric: { label: "NPS", value: 72, unit: "" },
  },
];

export const STRATEGY_LINKS: MarketingActionLink[] = [
  // 0 -> 1 (Universe -> Acquisition)
  {
    source: "node-0",
    target: "node-1",
    value: 20000,
    channelType: "PAID_MEDIA",
    status: "HEALTHY",
    financialNature: "EXPENSE",
    label: "Meta Ads - Prospección Cold",
    metadata: { cost: 5000, ctr: 1.2 },
  },
  {
    source: "node-0",
    target: "node-1",
    value: 15000,
    channelType: "ORGANIC_SOCIAL",
    status: "HEALTHY",
    financialNature: "NEUTRAL",
    label: "TikTok Viral Content",
  },
  {
    source: "node-0",
    target: "node-1",
    value: 5000,
    channelType: "PAID_MEDIA",
    status: "BOTTLENECK", // Example of bottleneck
    financialNature: "EXPENSE",
    label: "Google Ads - Search",
    metadata: { cost: 8000, cpc: 1.6 },
  },

  // 1 -> 2 (Acquisition -> Activation)
  {
    source: "node-1",
    target: "node-2",
    value: 4000,
    channelType: "OWNED_MEDIA",
    status: "HEALTHY",
    financialNature: "NEUTRAL",
    label: "Lead Magnet Pop-up",
  },
  {
    source: "node-1",
    target: "node-2",
    value: 2000,
    channelType: "PAID_MEDIA",
    status: "POTENTIAL", // Placeholder
    financialNature: "EXPENSE",
    label: "Retargeting Lead Gen",
  },

  // 2 -> 3 (Activation -> Nutrition)
  {
    source: "node-2",
    target: "node-3",
    value: 3000,
    channelType: "OWNED_MEDIA",
    status: "HEALTHY",
    financialNature: "NEUTRAL",
    label: "Email Sequence - Welcome",
  },

  // 3 -> 4 (Nutrition -> Conversion)
  {
    source: "node-3",
    target: "node-4",
    value: 300,
    channelType: "SALES_TEAM",
    status: "HEALTHY",
    financialNature: "REVENUE", // Generates revenue
    label: "Closer Calls",
  },

  // Cross-Stage Jump: 1 -> 4 (Acquisition -> Conversion)
  {
    source: "node-1",
    target: "node-4",
    value: 100,
    channelType: "PAID_MEDIA",
    status: "HEALTHY",
    financialNature: "EXPENSE", // Direct to offer
    label: "Retargeting - Direct Offer",
  },

  // 4 -> 5 (Conversion -> Adoption)
  {
    source: "node-4",
    target: "node-5",
    value: 400,
    channelType: "OWNED_MEDIA",
    status: "HEALTHY",
    financialNature: "NEUTRAL",
    label: "Onboarding Sequence",
  },

  // 5 -> 6 (Adoption -> Expansion)
  {
    source: "node-5",
    target: "node-6",
    value: 120,
    channelType: "OWNED_MEDIA",
    status: "BOTTLENECK",
    financialNature: "REVENUE",
    label: "Upsell Campaign",
  },

  // 6 -> 7 (Expansion -> Evangelization)
  {
    source: "node-6",
    target: "node-7",
    value: 35,
    channelType: "PARTNERS",
    status: "POTENTIAL",
    financialNature: "NEUTRAL",
    label: "Affiliate Program",
  },

  // Loopback: 7 -> 1 (Evangelization -> Acquisition)
  // Note: Visx/Sankey is typically acyclic. If Visx supports loops, we can add this.
  // If not, we might need to handle it visually or omit it for now to avoid breaking the layout.
  // For now, I will comment it out to be safe, as standard Sankeys are acyclic.
  /*
  {
    source: 'node-7',
    target: 'node-1',
    value: 350, // Leads generated by referrals
    channelType: 'PARTNERS',
    status: 'HEALTHY',
    financialNature: 'NEUTRAL',
    label: 'Referral Traffic'
  }
  */
];

export const MOCK_CONFIG: StrategyCanvasConfig = {
  nodes: STRATEGY_NODES,
  links: STRATEGY_LINKS,
};
