import { config } from "../config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface BookingLink {
    token: string;
    url: string;
    expires_at: string;
}

export const bookingLinksApi = {
    create: async (payload: { lead_id: string; event_slug: string; expiration_days: number }, token: string): Promise<BookingLink> => {
        const res = await fetchClient(`${API_URL}/api/v1/calendar/personalized-link`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Error creating booking link");
        return res.json();
    }
}
