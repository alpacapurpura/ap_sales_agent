"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useParams } from "next/navigation";
import Link from "next/link";
import { getActiveInterview } from "@/features/copilot/api/interview-api";

export function InterviewBanner() {
  const pathname = usePathname();
  const params = useParams();
  const tenantId = params.tenantId as string;

  const { data: active } = useQuery({
    queryKey: ["interview", "active"],
    queryFn: getActiveInterview,
    staleTime: 60_000,
  });

  if (!active || pathname.includes("/brand-studio/interview")) return null;

  return (
    <div className="mx-4 mt-2 flex items-center justify-between rounded-lg border border-purple-500 bg-[#1e1b4b] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <div className="h-2 w-2 animate-pulse rounded-full bg-purple-500" />
        <span className="text-sm text-white">
          Entrevista {active.domain_label} en curso
        </span>
        <span className="text-xs text-gray-400">
          ({active.bloques_completados.length}/{active.total_bloques} bloques)
        </span>
      </div>
      <Link
        href={`/${tenantId}/brand-studio/interview?session=${active.session_id}`}
        className="rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-purple-700"
      >
        Continuar →
      </Link>
    </div>
  );
}
