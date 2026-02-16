import { config } from "../config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface SchedulingLimits {
  max_advance_days: number;
  min_advance_hours: number;
}

export interface BookingConfig {
  buffer_minutes: number;
  max_per_day: number | null;
  guest_permissions: boolean;
}

export interface EventType {
  id: string;
  title: string;
  description: string;
  duration: number;
  slug: string;
  is_hidden: boolean;
  availability_id: string | null;
  calendar_id: string | null;
  scheduling_limits: SchedulingLimits;
  booking_config: BookingConfig;
  confirmation_button?: {
    enabled: boolean;
    text?: string;
    url?: string;
  };
}

export type EventTypeUpdate = Partial<EventType>;

export const eventTypesApi = {
  listEventTypes: async (token: string): Promise<EventType[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/event-types`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error fetching event types");
    return res.json();
  },

  createEventType: async (eventType: Omit<EventType, 'id'>, token: string): Promise<EventType> => {
    const res = await fetchClient(`${API_URL}/api/v1/event-types`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(eventType),
    });
    if (!res.ok) throw new Error("Error creating event type");
    return res.json();
  },

  updateEventType: async (id: string, update: EventTypeUpdate, token: string): Promise<EventType> => {
    const res = await fetchClient(`${API_URL}/api/v1/event-types/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error("Error updating event type");
    return res.json();
  },

  deleteEventType: async (id: string, token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/event-types/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error deleting event type");
  }
};
