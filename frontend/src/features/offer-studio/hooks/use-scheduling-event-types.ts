"use client";

import { useQuery } from "@tanstack/react-query";

import {
  schedulingEventTypesApi,
  type SchedulingEventType,
} from "../api/scheduling-event-types-api";

const QUERY_KEY = ["scheduling", "event-types"] as const;

/**
 * Consumes ``/api/v1/scheduling/event-types`` to populate the
 * ``scheduling-event-type-picker`` custom action in ``location.schema.ts``.
 *
 * Empty array during loading or when the tenant has not configured the
 * Scheduling module — the picker shows a CTA ("Configura Agenda →") in
 * that case.
 */
export function useSchedulingEventTypes() {
  const { data, isLoading, error } = useQuery<readonly SchedulingEventType[]>({
    queryKey: QUERY_KEY,
    queryFn: schedulingEventTypesApi.list,
    staleTime: 60 * 1000,
  });

  return {
    eventTypes: data ?? [],
    isLoading,
    error,
    /** True when the tenant has at least one enabled event type to reference. */
    hasConfiguredScheduling: (data ?? []).some((et) => et.enabled),
  };
}

export type { SchedulingEventType };
