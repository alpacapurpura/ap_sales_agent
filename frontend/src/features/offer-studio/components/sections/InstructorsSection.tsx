"use client";

import { SectionProps } from "../../types/section";
import { InstructorsSelector } from "../forms/instructors-selector";

export function InstructorsSection({ form }: SectionProps) {
  return (
    <InstructorsSelector 
      selectedInstructorIds={(form.watch("instructors") || []) as string[]}
      onUpdate={(ids) => form.setValue("instructors", ids, { shouldDirty: true, shouldValidate: true })}
    />
  );
}
