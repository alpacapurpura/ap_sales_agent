import type { ChannelDashboardData } from "../../../../types/metrics";

export type WebsiteDashboardTab = "overview" | "trafico" | "contenido" | "conversiones";

export type WebsiteTrafficSource = {
  source: string;
  sessions: number;
  percentage: number;
};

export type WebsiteDeviceSplit = {
  device: string;
  percentage: number;
};

export type WebsiteTopPage = {
  path: string;
  views: number;
  percentage: number;
};

export type WebsiteCountry = {
  country: string;
  sessions: number;
  percentage: number;
};

export type WebsiteExtraData = {
  traffic_sources?: WebsiteTrafficSource[];
  device_split?: WebsiteDeviceSplit[];
  top_pages?: WebsiteTopPage[];
  country?: WebsiteCountry[];
};

export type WebsiteData = ChannelDashboardData & {
  extraData?: WebsiteExtraData;
};
