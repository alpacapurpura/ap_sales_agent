"use client";

import { SectionProps } from "../../types/section";
import { SubscriptionDetailsForm } from "../forms/subscription-form";

export function SubscriptionDetailsSection({ form }: SectionProps) {
  return <SubscriptionDetailsForm form={form} />;
}
