"use client";

import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { InstructorsSelector } from "./instructors-selector";
import { KeyFigure } from "@/features/brand/types";

const InstructorsSchema = OfferSchema.pick({
  instructors: true
});

type InstructorsFormValues = Pick<OfferFormValues, "instructors">;

export interface InstructorsFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
  availableInstructors: KeyFigure[];
  onRefresh?: () => void;
}

function InstructorsContent({ form, availableInstructors, onRefresh }: { form: UseFormReturn<OfferFormValues>, availableInstructors: KeyFigure[], onRefresh?: () => void }) {
  return (
    <InstructorsSelector 
      selectedInstructorIds={(form.watch("instructors") || []) as string[]}
      onUpdate={(ids) => form.setValue("instructors", ids, { shouldDirty: true, shouldValidate: true })}
      availableInstructors={availableInstructors}
      onRefresh={onRefresh}
    />
  );
}

export function InstructorsForm({ defaultValues: propValues, onSave, availableInstructors, onRefresh }: InstructorsFormProps) {
  const defaultValues: InstructorsFormValues = {
    instructors: propValues?.instructors || []
  };

  const handleSave = async (data: InstructorsFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<InstructorsFormValues>
      schema={InstructorsSchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <InstructorsContent 
            form={form as unknown as UseFormReturn<OfferFormValues>} 
            availableInstructors={availableInstructors}
            onRefresh={onRefresh}
        />
      )}
    </SectionFormWrapper>
  );
}
