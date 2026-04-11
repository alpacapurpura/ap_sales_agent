// Landing status types — CONTRACT.md §6.4
import type { LandingJobStatus } from "./enums";

export interface LandingStatusResponse {
  offer_id: string;
  landing_page_id: string | null;
  is_generated: boolean;
  is_published: boolean;
  is_outdated: boolean;
  generated_at: string | null;
  offer_snapshot_version: string | null;
  offer_updated_at: string;
  job_id: string | null;
  job_status: LandingJobStatus;
  landing_url: string | null;
  editor_url: string | null;
  completion_percentage: number;
}

export interface LandingGenerateResponse {
  job_id: string;
  job_status: LandingJobStatus;
  offer_snapshot_version: string;
  queued_at: string;
}

export interface LandingPublishResponse {
  landing_page_id: string;
  is_published: boolean;
  landing_url: string;
  published_at: string;
}

export interface LandingUnpublishResponse {
  landing_page_id: string;
  is_published: boolean;
  unpublished_at: string;
}
