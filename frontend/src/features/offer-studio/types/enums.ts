// Offer Studio Header + Lifecycle Refactor — enums
// Source of truth: docs/features/2026-04-11-offer-header-refactor/CONTRACT.md §6.1

export const OFFER_LIFECYCLE_STATUS = [
  "draft",
  "active",
  "paused",
  "archived",
] as const;
export type OfferLifecycleStatus = (typeof OFFER_LIFECYCLE_STATUS)[number];

export const OFFER_ASSET_TYPE = [
  "flyer",
  "video",
  "carousel",
  "document",
  "image",
] as const;
export type OfferAssetType = (typeof OFFER_ASSET_TYPE)[number];

export const OFFER_ASSET_SOURCE = ["ai", "external"] as const;
export type OfferAssetSource = (typeof OFFER_ASSET_SOURCE)[number];

export const OFFER_ASSET_STATUS = [
  "draft",
  "processing",
  "ready",
  "error",
] as const;
export type OfferAssetStatus = (typeof OFFER_ASSET_STATUS)[number];

export const KNOWLEDGE_SOURCE_TYPE = [
  "pdf",
  "docx",
  "txt",
  "markdown",
  "video",
  "url_youtube",
  "url_article",
  "url_google_doc",
] as const;
export type KnowledgeSourceType = (typeof KNOWLEDGE_SOURCE_TYPE)[number];

export const KNOWLEDGE_SOURCE_STATUS = [
  "queued",
  "processing",
  "indexed",
  "error",
] as const;
export type KnowledgeSourceStatus = (typeof KNOWLEDGE_SOURCE_STATUS)[number];

export const LANDING_JOB_STATUS = [
  "idle",
  "queued",
  "running",
  "success",
  "error",
] as const;
export type LandingJobStatus = (typeof LANDING_JOB_STATUS)[number];
