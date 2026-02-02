import { config } from "../config";

const API_URL = config.api.baseUrl;

export interface LinkResolveResponse {
    valid: bool;
    type: string;
    tenant_name: string;
    tenant_avatar?: string;
    params: Record<string, any>;
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
}

export const publicApi = {
    resolveLink: async (token: string): Promise<LinkResolveResponse> => {
        const res = await fetch(`${API_URL}/api/v1/public/resolve/${token}`, {
            cache: 'no-store'
        });
        if (!res.ok) {
            if (res.status === 404) throw new Error("Link not found");
            throw new Error("Failed to resolve link");
        }
        return res.json();
    },

    getSlots: async (token: string, start: string, end: string): Promise<string[]> => {
        const params = new URLSearchParams({ start_date: start, end_date: end });
        const res = await fetch(`${API_URL}/api/v1/public/${token}/slots?${params}`, {
            cache: 'no-store'
        });
        if (!res.ok) throw new Error("Failed to fetch slots");
        const data = await res.json();
        return data.slots; // Expecting string[] of ISO datetimes
    },

    bookMeeting: async (token: string, data: BookingRequest) => {
        const res = await fetch(`${API_URL}/api/v1/public/${token}/book`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to book meeting");
        }
        return res.json();
    },

    // --- Event Type Public API ---

    resolveEventType: async (tenantSlug: string, eventSlug: string): Promise<EventTypeResolveResponse> => {
        const res = await fetch(`${API_URL}/api/v1/public/event-types/${tenantSlug}/${eventSlug}`, {
            cache: 'no-store'
        });
        if (!res.ok) {
            if (res.status === 404) throw new Error("Event type not found");
            throw new Error("Failed to resolve event type");
        }
        return res.json();
    },

    getEventTypeSlots: async (tenantSlug: string, eventSlug: string, start: string, end: string): Promise<string[]> => {
        const params = new URLSearchParams({ start_date: start, end_date: end });
        const res = await fetch(`${API_URL}/api/v1/public/event-types/${tenantSlug}/${eventSlug}/slots?${params}`, {
            cache: 'no-store'
        });
        if (!res.ok) throw new Error("Failed to fetch slots");
        const data = await res.json();
        return data.slots;
    },

    bookEventType: async (tenantSlug: string, eventSlug: string, data: BookingRequest) => {
        const res = await fetch(`${API_URL}/api/v1/public/event-types/${tenantSlug}/${eventSlug}/book`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to book meeting");
        }
        return res.json();
    }
};
