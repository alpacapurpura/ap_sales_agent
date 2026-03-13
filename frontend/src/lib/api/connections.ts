import { config } from "../config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface ChannelStatusResponse {
  is_connected: boolean;
  bot_name?: string;
  username?: string;
  config?: Record<string, any>;
}

export interface TelegramConnectRequest {
  token: string;
}

export interface TestResponse {
  status: string;
  message: string;
  data?: any;
}

export interface ShopifyConnectRequest {
  shop_url: string;
  access_token: string;
}

export interface ShopifyAuthUrlRequest {
  shop_url: string;
}

export interface ShopifyStatusResponse extends ChannelStatusResponse {
  shop_url?: string;
  scope?: string;
}

export interface MailerliteConnectRequest {
  api_key: string;
}

export interface MailerliteStatusResponse extends ChannelStatusResponse {
  account_info?: Record<string, any>;
}

export interface ManyChatConnectRequest {
  api_key: string;
}

export interface ManyChatStatusResponse extends ChannelStatusResponse {
  account_info?: Record<string, any>;
}

export interface GoogleAnalyticsStatusResponse extends ChannelStatusResponse {
  account_summary?: any[];
  is_configured?: boolean;
}

export interface GoogleAnalyticsConfigRequest {
  client_id: string;
  client_secret: string;
}

export interface MetaStatusResponse extends ChannelStatusResponse {
  name?: string;
  account_id?: string;
  is_configured?: boolean;
}

export interface YoutubeStatusResponse extends ChannelStatusResponse {
  is_configured?: boolean;
  channel_id?: string;
  channel_title?: string;
  channel_data?: Record<string, any>;
}

export const connectionsApi = {
  // ... existing methods ...

  // Google Analytics
  configureGoogleAnalytics: async (data: GoogleAnalyticsConfigRequest, token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/configure`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error configurando Google Analytics");
    }
    return res.json();
  },

  getGoogleAnalyticsStatus: async (token: string): Promise<GoogleAnalyticsStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Google Analytics");
    return res.json();
  },

  // Meta (Facebook/Instagram)
  getMetaStatus: async (token: string): Promise<MetaStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/meta/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Meta");
    return res.json();
  },

  getMetaAuthUrl: async (token: string, redirectUri?: string): Promise<{url: string, state: string}> => {
    let url = `${API_URL}/api/v1/connections/meta/auth-url`;
    if (redirectUri) {
        url += `?redirect_uri=${encodeURIComponent(redirectUri)}`;
    }
    const res = await fetchClient(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo URL de autorización");
    return res.json();
  },

  connectMeta: async (code: string, token: string, redirectUri?: string): Promise<any> => {
     const res = await fetchClient(`${API_URL}/api/v1/connections/meta/callback`, {
      method: "POST",
      headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ code: code, redirect_uri: redirectUri }),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando Meta");
    }
    return res.json();
  },

  disconnectMeta: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/meta/disconnect`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error desconectando Meta");
  },

  testMeta: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/meta/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión Meta");
    }
    return res.json();
  },

  getGoogleAnalyticsAuthUrl: async (token: string, redirectUri?: string): Promise<{url: string, state: string}> => {
    let url = `${API_URL}/api/v1/connections/google-analytics/auth-url`;
    if (redirectUri) {
        url += `?redirect_uri=${encodeURIComponent(redirectUri)}`;
    }
    const res = await fetchClient(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo URL de autorización");
    return res.json();
  },

  connectGoogleAnalytics: async (code: string, token: string, redirectUri?: string): Promise<any> => {
     const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/callback`, {
      method: "POST",
      headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ code: code, redirect_uri: redirectUri }),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando Google Analytics");
    }
    return res.json();
  },

  disconnectGoogleAnalytics: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/disconnect`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error desconectando Google Analytics");
  },

  testGoogleAnalytics: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google-analytics/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión Google Analytics");
    }
    return res.json();
  },


  // Shopify
  getShopifyStatus: async (token: string): Promise<ShopifyStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/shopify/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Shopify");
    return res.json();
  },

  generateShopifyAuthUrl: async (data: ShopifyAuthUrlRequest, token: string): Promise<{ auth_url: string }> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/shopify/generate-auth-url`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error generando URL de autorización");
    }
    return res.json();
  },

  connectShopify: async (data: ShopifyConnectRequest, token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/shopify/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando Shopify");
    }
    return res.json();
  },

  testShopify: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/shopify/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión Shopify");
    }
    return res.json();
  },

  disconnectShopify: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/shopify/disconnect`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Error desconectando Shopify");
  },

  getTelegramStatus: async (token: string): Promise<ChannelStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/telegram/status`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Telegram");
    return res.json();
  },

  connectTelegram: async (data: TelegramConnectRequest, token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/telegram/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando Telegram");
    }
    return res.json();
  },

  testTelegram: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/telegram/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión");
    }
    return res.json();
  },

  disconnectTelegram: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/telegram/disconnect`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Error desconectando Telegram");
  },

  // Google Calendar
  getCalendarStatus: async (token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Calendario");
    return res.json();
  },
  
  getGoogleAuthUrl: async (token: string, redirectUri?: string): Promise<{url: string, state: string}> => {
    let url = `${API_URL}/api/v1/connections/calendar/auth-url`;
    if (redirectUri) {
        url += `?redirect_uri=${encodeURIComponent(redirectUri)}`;
    }
    const res = await fetchClient(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo URL de autorización");
    return res.json();
  },

  connectGoogle: async (code: string, token: string, redirectUri?: string): Promise<any> => {
     const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/callback`, {
      method: "POST",
      headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ code: code, redirect_uri: redirectUri }),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando Google Calendar");
    }
    return res.json();
  },

  disconnectCalendar: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/disconnect`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error desconectando Calendario");
  },

  testCalendar: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión");
    }
    return res.json();
  },

  listAppointments: async (start: string, end: string, token: string): Promise<any[]> => {
      const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/appointments?start_date=${start}&end_date=${end}`, {
          headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Error obteniendo citas");
      return res.json();
  },

  generateBookingLink: async (token: string): Promise<{ token: string; url: string }> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/link`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error generando enlace");
    return res.json();
  },

  // Gmail
  getGmailStatus: async (token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/gmail/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Gmail");
    return res.json();
  },

  getGmailAuthUrl: async (token: string, redirectUri?: string): Promise<{url: string, state: string}> => {
    let url = `${API_URL}/api/v1/connections/gmail/auth-url`;
    if (redirectUri) {
        url += `?redirect_uri=${encodeURIComponent(redirectUri)}`;
    }
    const res = await fetchClient(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo URL de autorización");
    return res.json();
  },

  connectGmail: async (code: string, token: string, redirectUri?: string): Promise<any> => {
     const res = await fetchClient(`${API_URL}/api/v1/connections/gmail/callback`, {
      method: "POST",
      headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ code: code, redirect_uri: redirectUri }),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando Gmail");
    }
    return res.json();
  },

  disconnectGmail: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/gmail/disconnect`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error desconectando Gmail");
  },

  testGmail: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/gmail/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión");
    }
    return res.json();
  },

  // MailerLite
  getMailerLiteStatus: async (token: string): Promise<MailerliteStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/mailerlite/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de MailerLite");
    return res.json();
  },

  connectMailerLite: async (data: MailerliteConnectRequest, token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/mailerlite/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando MailerLite");
    }
    return res.json();
  },

  testMailerLite: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/mailerlite/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión MailerLite");
    }
    return res.json();
  },

  disconnectMailerLite: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/mailerlite/disconnect`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Error desconectando MailerLite");
  },

  // ManyChat
  getManyChatStatus: async (token: string): Promise<ManyChatStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/manychat/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de ManyChat");
    return res.json();
  },

  connectManyChat: async (data: ManyChatConnectRequest, token: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/manychat/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando ManyChat");
    }
    return res.json();
  },

  testManyChat: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/manychat/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión ManyChat");
    }
    return res.json();
  },

  disconnectManyChat: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/manychat/disconnect`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Error desconectando ManyChat");
  },

  // Google Workspace (Unified OAuth)
  getGoogleWorkspaceAuthUrl: async (token: string): Promise<{ url: string; state: string }> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google/workspace/auth-url`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo URL de autorización de Google");
    return res.json();
  },

  connectGoogleWorkspace: async (code: string, token: string): Promise<{ status: string; email: string }> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google/workspace/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error conectando Google Workspace");
    }
    return res.json();
  },

  getGoogleWorkspaceStatus: async (token: string): Promise<{
    is_connected: boolean;
    email?: string;
    services: Record<string, { is_active: boolean; has_credentials: boolean }>;
  }> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google/workspace/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de Google Workspace");
    return res.json();
  },

  toggleGoogleWorkspaceService: async (service: string, isActive: boolean, token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google/workspace/services/${service}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ is_active: isActive }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error actualizando servicio");
    }
  },

  disconnectGoogleWorkspace: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/google/workspace/`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error desconectando Google Workspace");
  },

  // YouTube
  getYoutubeStatus: async (token: string): Promise<YoutubeStatusResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/youtube/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo estado de YouTube");
    return res.json();
  },

  getYoutubeAuthUrl: async (token: string, redirectUri?: string): Promise<{url: string, state: string}> => {
    let url = `${API_URL}/api/v1/connections/youtube/auth-url`;
    if (redirectUri) {
        url += `?redirect_uri=${encodeURIComponent(redirectUri)}`;
    }
    const res = await fetchClient(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error obteniendo URL de autorización");
    return res.json();
  },

  connectYoutube: async (code: string, token: string, redirectUri?: string): Promise<any> => {
     const res = await fetchClient(`${API_URL}/api/v1/connections/youtube/callback`, {
      method: "POST",
      headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ code: code, redirect_uri: redirectUri }),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error conectando YouTube");
    }
    return res.json();
  },

  disconnectYoutube: async (token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/youtube/disconnect`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error desconectando YouTube");
  },

  testYoutube: async (token: string): Promise<TestResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/youtube/test`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error probando conexión YouTube");
    }
    return res.json();
  },

  configureYoutube: async (token: string, clientId: string, clientSecret: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/youtube/configure`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error configurando YouTube");
    }
    return res.json();
  }
};
