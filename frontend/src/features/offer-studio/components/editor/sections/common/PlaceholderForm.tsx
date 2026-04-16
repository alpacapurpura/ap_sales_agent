import React from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import type { OfferFormValues } from "../../../../types/schema";
import type { UseFormReturn } from "react-hook-form";

export interface PlaceholderFormProps {
  sectionId?: string;
  title?: string;
  children?: React.ReactNode;
  defaultValues?: Partial<OfferFormValues>;
  onSave?: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: UseFormReturn<OfferFormValues>;
}

export const PlaceholderForm = ({
  sectionId,
  title,
  children,
  defaultValues,
  onSave,
  form,
}: PlaceholderFormProps) => {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title || "Sección en desarrollo"}</CardTitle>
      </CardHeader>
      <CardContent>
        {children || (
          <div className="p-4 border rounded bg-muted/20 text-muted-foreground">
            Form configuration for {sectionId || "unknown section"}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
