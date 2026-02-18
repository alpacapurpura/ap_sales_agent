"use client";

import { SectionProps } from "../../types/section";
import { EventDetailsForm } from "../forms/event-form";

export function EventDetailsSection({ form }: SectionProps) {
  return <EventDetailsForm form={form} />;
}
