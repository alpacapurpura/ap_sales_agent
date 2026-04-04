export const TEST_TENANT_ID = process.env.E2E_TENANT_ID!;
export const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';

export const ROUTES = {
  brandStudio: (tenantId: string, section = 'esencia') =>
    `/${tenantId}/brand-studio/${section}`,
  offerStudio: (tenantId: string) => `/${tenantId}/offer-studio`,
  growthStudio: (tenantId: string, stage = 'atraccion-captura') =>
    `/${tenantId}/growth-studio/${stage}`,
  sales: (tenantId: string) => `/${tenantId}/sales`,
  settings: (tenantId: string) => `/${tenantId}/settings`,
  dashboard: (tenantId: string) => `/${tenantId}`,
} as const;

export const BRAND_SECTIONS = [
  'esencia',
  'estrategia',
  'publico',
  'tono-y-voz',
  'identidad-creativa',
  'assets',
] as const;

export const GROWTH_STAGES = [
  'atraccion-captura',
  'nutricion-oportunidad',
  'ventas',
  'adopcion',
  'expansion-evangelizacion',
  'campanas',
] as const;
