"use client";

import { SectionProps } from "../../types/section";
import { ServiceDetailsForm } from "../forms/service-form";

export function ServiceDetailsSection({ form }: SectionProps) {
  return <ServiceDetailsForm form={form} />;
}
