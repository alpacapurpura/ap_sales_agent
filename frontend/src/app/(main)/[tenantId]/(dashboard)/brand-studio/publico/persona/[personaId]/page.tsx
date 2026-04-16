"use client";

import { use } from "react";

import { PersonaDetailView } from "@/features/brand/components/views/PersonaDetailView";

export default function PersonaDetailPage({
  params,
}: {
  params: Promise<{ tenantId: string; personaId: string }>;
}) {
  const { personaId } = use(params);
  return <PersonaDetailView personaId={personaId} />;
}
