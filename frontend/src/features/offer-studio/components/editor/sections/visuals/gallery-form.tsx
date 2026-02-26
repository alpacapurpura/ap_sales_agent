"use client";

import { useParams } from "next/navigation";
import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { OfferGallerySection } from "../../components/offer-gallery-section";
import { Card, CardContent } from "@/components/ui/card";

// Gallery mostly updates assets, so we use that part of the schema
const GallerySchema = OfferSchema.pick({
  assets: true
});

type GalleryFormValues = Pick<OfferFormValues, "assets">;

export interface GalleryFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
}

function GalleryContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const params = useParams();
  const offerId = params?.offerId as string;

  return (
    <Card>
      <CardContent className="pt-6">
        {/* OfferGallerySection handles its own logic, likely updating assets via API directly or context */}
        {/* If it needs to update the form, it might need to be refactored to accept onChange or control */}
        {/* For now, preserving existing behavior */}
        <OfferGallerySection offerId={offerId} />
      </CardContent>
    </Card>
  );
}

export function GalleryForm({ defaultValues: propValues, onSave }: GalleryFormProps) {
  const defaultValues: GalleryFormValues = {
    assets: propValues?.assets || []
  };

  const handleSave = async (data: GalleryFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<GalleryFormValues>
      schema={GallerySchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <GalleryContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
