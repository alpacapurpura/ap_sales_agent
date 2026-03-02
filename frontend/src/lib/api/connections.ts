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

export const connectionsApi = {
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
  }
};
