import { config } from "../config";
import { fetchClient } from "../http-client";

import type { AuthorityItem } from "./authority-item";
import type { TeamMember } from "./team-member";
import type { Testimonial } from "./testimonial";

const API_URL = config.api.baseUrl;

export type SourceTable = "testimonial" | "authority_item" | "team_member";
export type SurfaceType =
  | "brand_homepage"
  | "offer"
  | "landing_page"
  | "email_sequence"
  | "sales_agent_kb";

export interface Placement {
  id: string;
  tenant_id: string;
  source_table: SourceTable;
  source_id: string;
  surface_type: SurfaceType;
  surface_ref_id: string | null;
  sort_order: number;
  is_visible: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface PlacementCreateDTO {
  source_table: SourceTable;
  source_id: string;
  surface_type: SurfaceType;
  surface_ref_id?: string | null;
  sort_order?: number;
  is_visible?: boolean;
}

export type PlacementUpdateDTO = Partial<Pick<Placement, "sort_order" | "is_visible">>;

export interface PlacedTestimonial {
  testimonial: Testimonial;
  placement: Placement;
}

export interface PlacedAuthorityItem {
  authority_item: AuthorityItem;
  placement: Placement;
}

export interface PlacedTeamMember {
  team_member: TeamMember;
  placement: Placement;
}

export interface ResolvedSocialProof {
  testimonials: PlacedTestimonial[];
  authority_items: PlacedAuthorityItem[];
  team_members: PlacedTeamMember[];
}

const BASE = `${API_URL}/api/v1/social-proof/placements`;

export const placementApi = {
  listBySource: async (
    token: string,
    sourceTable: SourceTable,
    sourceId: string,
  ): Promise<Placement[]> => {
    const res = await fetchClient(
      `${BASE}/?source_table=${encodeURIComponent(sourceTable)}&source_id=${encodeURIComponent(sourceId)}`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    if (!res.ok) throw new Error("Failed to list placements");
    return res.json() as Promise<Placement[]>;
  },

  create: async (token: string, data: PlacementCreateDTO): Promise<Placement> => {
    const res = await fetchClient(`${BASE}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create placement");
    return res.json() as Promise<Placement>;
  },

  patch: async (token: string, id: string, data: PlacementUpdateDTO): Promise<Placement> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update placement");
    return res.json() as Promise<Placement>;
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete placement");
  },

  forSurface: async (
    token: string,
    params: {
      surfaceType: SurfaceType;
      surfaceRefId?: string | null;
      includeBrand?: boolean;
    },
  ): Promise<ResolvedSocialProof> => {
    const qs = new URLSearchParams({ surface_type: params.surfaceType });
    if (params.surfaceRefId) qs.set("surface_ref_id", params.surfaceRefId);
    if (params.includeBrand) qs.set("include_brand", "true");
    const res = await fetchClient(`${BASE}/for-surface?${qs.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to resolve social proof for surface");
    return res.json() as Promise<ResolvedSocialProof>;
  },
};
