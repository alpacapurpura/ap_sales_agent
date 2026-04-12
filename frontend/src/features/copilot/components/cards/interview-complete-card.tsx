"use client";

import { useRouter, useParams } from "next/navigation";

interface InterviewCompleteCardProps {
  healthScore: number;
  redirect: string;
}

export function InterviewCompleteCard({ healthScore, redirect }: InterviewCompleteCardProps) {
  const router = useRouter();
  const params = useParams();
  const tenantId = params.tenantId as string;

  return (
    <div className="rounded-xl border border-green-500 bg-green-900/20 p-4 text-center">
      <div className="text-2xl font-bold text-green-500">{healthScore}%</div>
      <div className="mt-1 text-xs text-green-400">¡Tu marca está lista!</div>
      <button
        onClick={() => router.push(`/${tenantId}${redirect}`)}
        className="mt-3 rounded-md bg-green-600 px-4 py-2 text-xs font-medium text-white hover:bg-green-700"
      >
        Ver Brand Studio →
      </button>
    </div>
  );
}
