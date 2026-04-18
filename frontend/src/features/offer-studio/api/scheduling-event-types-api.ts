import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

/**
 * Event type from ``/api/v1/scheduling/event-types``. The picker shows
 * ``name``, ``duration_minutes`` and ``enabled``. The full backend shape
 * lives in ``backend/src/modules/scheduling/domain/event_type_schema.py``.
 */
export interface SchedulingEventType {
  readonly id: string;
  readonly name: string;
  readonly duration_minutes: number;
  readonly enabled: boolean;
  readonly location: string | null;
  readonly description: string | null;
}

export const schedulingEventTypesApi = {
  list: async (): Promise<readonly SchedulingEventType[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/scheduling/event-types`);
    if (!res.ok) throw new Error("Failed to fetch scheduling event types");
    return res.json() as Promise<readonly SchedulingEventType[]>;
  },
};
