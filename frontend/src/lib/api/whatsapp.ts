import { config } from "../config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface WhatsAppProviderStatus {
  status: "connected" | "disconnected" | "connecting" | "error";
  profile?: {
    first_name?: string;
    remote_jid?: string;
    [key: string]: any;
  };
  detail?: string;
}

export interface WhatsAppDashboardStatus {
  evolution: WhatsAppProviderStatus;
  meta: WhatsAppProviderStatus;
}

export interface WhatsAppQR {
  code?: string; // base64
  pairingCode?: string;
  status?: string;
  count?: number;
  detail?: string;
}

export const whatsappApi = {
  getStatus: async (token: string): Promise<WhatsAppDashboardStatus> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/whatsapp/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error checking status");
    return res.json();
  },

  createSession: async (token: string, provider: "evolution" | "meta" = "evolution"): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/whatsapp/session`, {
      method: "POST",
      headers: { 
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ provider })
    });
    if (!res.ok) throw new Error("Error creating session");
  },

  getQR: async (token: string): Promise<WhatsAppQR> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/whatsapp/qr`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error fetching QR");
    return res.json();
  },

  disconnect: async (token: string, provider: "evolution" | "meta" = "evolution"): Promise<void> => {
    // Pass provider as query param
    const res = await fetchClient(`${API_URL}/api/v1/connections/whatsapp/session?provider=${provider}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error disconnecting");
  },
};
