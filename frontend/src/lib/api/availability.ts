import { config } from "../config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface TimeRange {
  start: string;
  end: string;
}

export interface DaySchedule {
  active: boolean;
  ranges: TimeRange[];
}

export interface WeeklySchedule {
  monday: DaySchedule;
  tuesday: DaySchedule;
  wednesday: DaySchedule;
  thursday: DaySchedule;
  friday: DaySchedule;
  saturday: DaySchedule;
  sunday: DaySchedule;
}

export interface AvailabilitySchedule {
  id: string;
  name: string;
  is_default: boolean;
  timezone: string;
  schedule: WeeklySchedule;
}

export type ScheduleUpdate = Partial<AvailabilitySchedule>;

export const availabilityApi = {
  listSchedules: async (token: string): Promise<AvailabilitySchedule[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/schedules`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error fetching schedules");
    return res.json();
  },

  createSchedule: async (
    schedule: Omit<AvailabilitySchedule, "id">,
    token: string,
  ): Promise<AvailabilitySchedule> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/schedules`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(schedule),
    });
    if (!res.ok) throw new Error("Error creating schedule");
    return res.json();
  },

  updateSchedule: async (
    id: string,
    update: ScheduleUpdate,
    token: string,
  ): Promise<AvailabilitySchedule> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/schedules/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(update),
    });
    if (!res.ok) throw new Error("Error updating schedule");
    return res.json();
  },

  deleteSchedule: async (id: string, token: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/calendar/schedules/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Error deleting schedule");
  },
};
