// Offer assets types — CONTRACT.md §6.5
import type { OfferAssetSource, OfferAssetStatus, OfferAssetType } from "./enums";

export type AssetSortKey = "created_desc" | "created_asc" | "name_asc" | "name_desc";

export interface AssetListQuery {
  search?: string;
  type?: OfferAssetType;
  source?: OfferAssetSource;
  sort?: AssetSortKey;
  limit?: number;
  offset?: number;
}

export interface AssetResponse {
  id: string;
  offer_id: string;
  name: string;
  type: OfferAssetType;
  source: OfferAssetSource;
  status: OfferAssetStatus;
  file_url: string | null;
  thumbnail_url: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  metadata: Record<string, unknown>;
  editable_in_puck: boolean;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AssetListResponse {
  items: AssetResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AssetGeneratePayload {
  type: OfferAssetType;
  name?: string;
  prompt_params?: Record<string, unknown>;
}

export interface AssetUpdatePayload {
  name?: string;
  metadata?: Record<string, unknown>;
}
