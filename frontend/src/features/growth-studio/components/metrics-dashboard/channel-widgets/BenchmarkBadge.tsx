"use client";

import { cn } from "@/lib/utils";

import type { BenchmarkRange } from "../../../types/metrics";

interface BenchmarkBadgeProps {
  value: number;
  benchmark: BenchmarkRange;
  higherIsBetter: boolean;
}

/**
 *
 */
export function BenchmarkBadge({ value, benchmark, higherIsBetter }: BenchmarkBadgeProps) {
  const { status, label } = getBenchmarkStatus(value, benchmark, higherIsBetter);

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        status === "good" && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
        status === "average" && "bg-amber-500/10 text-amber-600 dark:text-amber-400",
        status === "poor" && "bg-red-500/10 text-red-600 dark:text-red-400",
      )}
      title={benchmark.interpretation}
    >
      {label}
    </span>
  );
}

type BenchmarkStatus = "good" | "average" | "poor";

function getBenchmarkStatus(
  value: number,
  benchmark: BenchmarkRange,
  higherIsBetter: boolean,
): { status: BenchmarkStatus; label: string } {
  const { low, median, high } = benchmark;

  if (higherIsBetter) {
    if (value >= high) {
      const pct = Math.round(((value - median) / median) * 100);
      return { status: "good", label: `${pct}% mejor que promedio` };
    }
    if (value >= low) {
      return { status: "average", label: "En promedio" };
    }
    const pct = Math.round(((median - value) / median) * 100);
    return { status: "poor", label: `${pct}% bajo promedio` };
  }

  // Lower is better (e.g., CPC, CPA)
  if (value <= low) {
    const pct = Math.round(((median - value) / median) * 100);
    return { status: "good", label: `${pct}% mejor que promedio` };
  }
  if (value <= high) {
    return { status: "average", label: "En promedio" };
  }
  const pct = Math.round(((value - median) / median) * 100);
  return { status: "poor", label: `${pct}% sobre promedio` };
}
