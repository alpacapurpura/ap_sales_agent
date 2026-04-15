import type { ChannelDashboardData } from "../../../../types/metrics";

export type WebsiteDashboardTab = "overview" | "trafico" | "contenido" | "conversiones";

export interface WebsiteTrafficSource {
  source: string;
  sessions: number;
  percentage: number;
}

export interface WebsiteDeviceSplit {
  device: string;
  percentage: number;
}

export interface WebsiteTopPage {
  path: string;
  views: number;
  percentage: number;
}

export interface WebsiteCountry {
  country: string;
  sessions: number;
  percentage: number;
}

export interface WebsiteExtraData {
  traffic_sources?: WebsiteTrafficSource[];
  device_split?: WebsiteDeviceSplit[];
  top_pages?: WebsiteTopPage[];
  country?: WebsiteCountry[];
}

export type WebsiteData = ChannelDashboardData & {
  extraData?: WebsiteExtraData;
};
