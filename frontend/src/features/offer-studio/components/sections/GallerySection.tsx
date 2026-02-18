"use client";

import { useParams } from "next/navigation";
import { SectionProps } from "../../types/section";
import { OfferGallerySection } from "../offer-gallery-section";
import { Card, CardContent } from "@/components/ui/card";

export function GallerySection({ form }: SectionProps) {
  const params = useParams();
  const offerId = params?.offerId as string;

  return (
    <Card>
      <CardContent className="pt-6">
        <OfferGallerySection offerId={offerId} />
      </CardContent>
    </Card>
  );
}
