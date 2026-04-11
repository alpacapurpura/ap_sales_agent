// Knowledge source types — CONTRACT.md §6.6
import type {
  KnowledgeSourceStatus,
  KnowledgeSourceType,
} from "./enums";

export interface KnowledgeListQuery {
  search?: string;
  type?: KnowledgeSourceType;
}

export interface KnowledgeSourceResponse {
  id: string;
  offer_id: string;
  name: string;
  type: KnowledgeSourceType;
  status: KnowledgeSourceStatus;
  source_url: string | null;
  file_url: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  indexed_chunk_count: number;
  last_indexed_at: string | null;
  metadata: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface KnowledgeListResponse {
  items: KnowledgeSourceResponse[];
  total: number;
}

export interface KnowledgeUrlIngestPayload {
  url: string;
  name?: string;
}
