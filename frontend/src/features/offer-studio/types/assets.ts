// Offer assets types — CONTRACT.md §6.5
import type { OfferAssetSource, OfferAssetStatus, OfferAssetType } from "./enums";

export type AssetSortKey = "created_desc" | "created_asc" | "name_asc" | "name_desc";

export interface AssetListQuery {
  search?: string;
  type?: OfferAssetType;
  source?: OfferAssetSource;
  /** When set, filters to assets bound to this edition + shared-across-edition assets. */
  edition_id?: string;
  sort?: AssetSortKey;
  limit?: number;
  offset?: number;
}

export interface AssetResponse {
  id: string;
  offer_id: string;
  /** Nullable: offer-level assets have no edition. */
  edition_id: string | null;
  /** When true, this asset is visible from every edition's gallery. */
  shared_across_editions: boolean;
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
  edition_id?: string;
  shared_across_editions?: boolean;
}

export interface AssetUpdatePayload {
  name?: string;
  metadata?: Record<string, unknown>;
  edition_id?: string | null;
  shared_across_editions?: boolean;
}
