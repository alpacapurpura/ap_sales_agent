import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface MetaAssetsResponse {
  pages: FacebookPageAsset[];
  instagram_accounts: InstagramAccountAsset[];
  ads_accounts: MetaAdsAccountAsset[];
  pixels: MetaPixelAsset[];
  whatsapp_accounts: WhatsAppBusinessAsset[];
  warnings?: string[];
}

export interface FacebookPageAsset {
  page_id: string;
  page_name: string;
  category?: string;
  picture_url?: string;
  fan_count?: number;
  instagram_account_id?: string;
  instagram_username?: string;
  is_active: boolean;
  has_credentials: boolean;
}

export interface InstagramAccountAsset {
  ig_account_id: string;
  ig_username: string;
  profile_picture_url?: string;
  follower_count?: number;
  linked_page_id?: string;
  linked_page_name?: string;
  is_active: boolean;
  has_credentials: boolean;
}

export interface MetaAdsAccountAsset {
  ad_account_id: string;
  ad_account_name: string;
  currency?: string;
  account_status?: number;
  is_active: boolean;
  has_credentials: boolean;
}

export interface MetaPixelAsset {
  pixel_id: string;
  pixel_name: string;
  linked_ad_account_id?: string;
  is_active: boolean;
  has_credentials: boolean;
}

export interface WhatsAppPhoneNumber {
  phone_number_id: string;
  display_phone_number?: string;
  verified_name?: string;
  quality_rating?: string;
}

export interface WhatsAppBusinessAsset {
  waba_id: string;
  waba_name: string;
  currency?: string;
  timezone_id?: string;
  business_id?: string;
  business_name?: string;
  phone_numbers: WhatsAppPhoneNumber[];
  is_active: boolean;
  has_credentials: boolean;
}

/**
 *
 */
export async function fetchMetaAssets(token: string): Promise<MetaAssetsResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/connections/meta/assets`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch Meta assets");
  return res.json() as Promise<MetaAssetsResponse>;
}

/**
 *
 */
export async function syncMetaAssets(token: string): Promise<MetaAssetsResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/connections/meta/assets/sync`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail || "Error sincronizando activos");
  }
  return res.json() as Promise<MetaAssetsResponse>;
}

/**
 *
 */
export async function toggleMetaAsset(
  token: string,
  channelType: string,
  assetId: string,
  isActive: boolean,
): Promise<void> {
  const res = await fetchClient(
    `${API_URL}/api/v1/connections/meta/assets/${channelType}/${assetId}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ is_active: isActive }),
    },
  );
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail || "Error actualizando activo");
  }
}
