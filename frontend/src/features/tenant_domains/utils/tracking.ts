import { config } from "@/lib/config";

export interface TrackingConfig {
  gtm_container_id: string | null;
  gtm_server_url: string | null;
  meta_pixel_id: string | null;
  ga_measurement_id: string | null;
}

export async function getTrackingConfig(tenantId: string): Promise<TrackingConfig | null> {
  try {
    const res = await fetch(
      `${config.api.baseUrl}/api/v1/public/tracking/${tenantId}`,
      { next: { revalidate: 300 } }, // 5 min cache
    );
    if (!res.ok) return null;
    return res.json() as Promise<TrackingConfig>;
  } catch {
    return null;
  }
}
