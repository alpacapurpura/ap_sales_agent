"use client";

import { use } from "react";
import { AvatarSelectionView } from "@/features/offer-studio/components/views/avatar-selection-view";

export default function AvatarPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return <AvatarSelectionView offerId={id} />;
}
