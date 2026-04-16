import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface LinkResolveResponse {
  valid: boolean;
  type: string;
  tenant_name: string;
  tenant_avatar?: string;
  params: Record<string, unknown>;
}

export interface BookingLinkResolveResponse {
  valid: boolean;
  event_slug: string;
  lead_name?: string;
  lead_email?: string;
  lead_phone?: string;
  lead_id: string;
  expires_at: string;
}

export interface Slot {
  start: string; // ISO String
  end: string;
}

export interface BookingRequest {
  slot_time: string; // ISO
  duration_minutes: number;
  name: string;
  email: string;
  phone?: string;
  notes?: string;
  booking_token?: string;
}

export interface EventTypeResolveResponse {
  event_type: {
    id: string;
    title: string;
    description?: string;
    duration: number;
    slug: string;
    locations: Location[];
    scheduling_limits: {
      max_advance_days: number;
    };
    confirmation_button?: {
      enabled: boolean;
      url?: string;
      text?: string;
    };
  };
  tenant_name: string;
  tenant_avatar?: string;
}

interface Location {
  id?: string;
  name?: string;
  type?: string;
  [key: string]: unknown;
}

export const publicApi = {
  resolveLink: async (token: string): Promise<LinkResolveResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/scheduling/public/resolve/${token}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      if (res.status === 404) throw new Error("Link not found");
      throw new Error("Failed to resolve link");
    }
    return res.json() as Promise<LinkResolveResponse>;
  },

  resolveBookingLink: async (token: string): Promise<BookingLinkResolveResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/scheduling/public/booking-links/${token}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      const err = (await res.json()) as { detail?: string };
      throw new Error(err.detail || "Link not found or expired");
    }
    return res.json() as Promise<BookingLinkResolveResponse>;
  },

  getSlots: async (token: string, start: string, end: string): Promise<string[]> => {
    const params = new URLSearchParams({ start_date: start, end_date: end });
    const res = await fetchClient(`${API_URL}/api/v1/scheduling/public/${token}/slots?${params}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch slots");
    const data = (await res.json()) as { slots: string[] };
    return data.slots; // Expecting string[] of ISO datetimes
  },

  bookMeeting: async (token: string, data: BookingRequest): Promise<Record<string, unknown>> => {
    const res = await fetchClient(`${API_URL}/api/v1/scheduling/public/${token}/book`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const err = (await res.json()) as { detail?: string };
      throw new Error(err.detail || "Failed to book meeting");
    }
    return res.json() as Promise<Record<string, unknown>>;
  },

  // --- Event Type Public API ---

  resolveEventType: async (
    tenantSlug: string,
    eventSlug: string,
  ): Promise<EventTypeResolveResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/scheduling/public/event-types/${tenantSlug}/${eventSlug}`,
      {
        cache: "no-store",
      },
    );
    if (!res.ok) {
      if (res.status === 404) throw new Error("Event type not found");
      throw new Error("Failed to resolve event type");
    }
    return res.json() as Promise<EventTypeResolveResponse>;
  },

  getEventTypeSlots: async (
    tenantSlug: string,
    eventSlug: string,
    start: string,
    end: string,
  ): Promise<string[]> => {
    const params = new URLSearchParams({ start_date: start, end_date: end });
    const res = await fetchClient(
      `${API_URL}/api/v1/scheduling/public/event-types/${tenantSlug}/${eventSlug}/slots?${params}`,
      {
        cache: "no-store",
      },
    );
    if (!res.ok) throw new Error("Failed to fetch slots");
    const data = (await res.json()) as { slots: string[] };
    return data.slots;
  },

  bookEventType: async (
    tenantSlug: string,
    eventSlug: string,
    data: BookingRequest,
  ): Promise<Record<string, unknown>> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/scheduling/public/event-types/${tenantSlug}/${eventSlug}/book`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
    );

    if (!res.ok) {
      const err = (await res.json()) as { detail?: string };
      throw new Error(err.detail || "Failed to book meeting");
    }
    return res.json() as Promise<Record<string, unknown>>;
  },
};
