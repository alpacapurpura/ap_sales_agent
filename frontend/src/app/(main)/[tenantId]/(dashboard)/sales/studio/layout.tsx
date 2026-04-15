"use client";

import { useParams } from "next/navigation";

import { CloserLayout } from "@/features/closer-studio/components/closer-layout";

export default function StudioLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const tenantId = (params?.tenantId as string) ?? "";

  return <CloserLayout tenantId={tenantId}>{children}</CloserLayout>;
}
