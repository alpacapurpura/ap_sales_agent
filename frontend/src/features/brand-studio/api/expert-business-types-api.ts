import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

/** Must match ``ExpertBusinessType`` StrEnum on the backend. */
export type ExpertBusinessType =
  | "consultor_asesor"
  | "coach_mentor"
  | "educador_infoproductor"
  | "agencia_dfy"
  | "host_comunidad"
  | "host_experiencia"
  | "creador_contenido"
  | "product_maker"
  | "saas_founder";

export const EXPERT_BUSINESS_TYPE_VALUES: readonly ExpertBusinessType[] = [
  "consultor_asesor",
  "coach_mentor",
  "educador_infoproductor",
  "agencia_dfy",
  "host_comunidad",
  "host_experiencia",
  "creador_contenido",
  "product_maker",
  "saas_founder",
] as const;

export interface ExpertBusinessTypeMetadata {
  readonly business_type: ExpertBusinessType;
  readonly label_es: string;
  readonly description_es: string;
  readonly sells_es: string;
  readonly icon_name: string;
  readonly examples_es: readonly string[];
}

export interface ExpertBusinessTypesCatalogResponse {
  readonly version: string;
  readonly business_types: readonly ExpertBusinessTypeMetadata[];
}

export const expertBusinessTypesApi = {
  fetchCatalog: async (): Promise<ExpertBusinessTypesCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/expert-business-types/catalog`);
    if (!res.ok) throw new Error("Failed to fetch expert-business-types catalog");
    return res.json() as Promise<ExpertBusinessTypesCatalogResponse>;
  },
};
