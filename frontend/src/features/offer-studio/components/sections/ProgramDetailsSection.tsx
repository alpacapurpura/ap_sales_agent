"use client";

import { SectionProps } from "../../types/section";
import { ProgramDetailsForm } from "../forms/program-form";

export function ProgramDetailsSection({ form }: SectionProps) {
  return <ProgramDetailsForm form={form} />;
}
