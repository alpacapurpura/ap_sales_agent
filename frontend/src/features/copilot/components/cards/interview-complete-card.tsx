"use client";

import { useRouter, useParams } from "next/navigation";
import { useCopilotStore } from "../../store/copilot-store";

interface InterviewCompleteCardProps {
  healthScore: number;
  redirect: string;
}

const DOMAIN_LABELS: Record<string, string> = {
  "/brand-studio": "Brand Studio",
  "/offer-studio": "Offer Studio",
};

export function InterviewCompleteCard({ healthScore, redirect }: InterviewCompleteCardProps) {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.tenantId as string;
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const clearInterview = useCopilotStore((s) => s.clearInterview);

  const label = DOMAIN_LABELS[redirect] ?? "el editor";

  const handleClick = () => {
    clearInterview();
    setSidebarState("open");
    router.push(`/${tenantId}${redirect}`);
  };

  return (
    <div className="rounded-xl border border-green-500 bg-green-900/20 p-4 text-center">
      <div className="text-2xl font-bold text-green-500">{healthScore}%</div>
      <div className="mt-1 text-xs text-green-400">¡Tu perfil está completo!</div>
      <button
        onClick={handleClick}
        className="mt-3 rounded-md bg-green-600 px-4 py-2 text-xs font-medium text-white hover:bg-green-700"
      >
        Ver {label} →
      </button>
    </div>
  );
}
