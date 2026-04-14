"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface DateRangePickerProps {
  rangeDays: number;
  onRangeChange: (days: number) => void;
}

const RANGES = [
  { value: 7, label: "7d" },
  { value: 30, label: "30d" },
  { value: 90, label: "90d" },
] as const;

export function DateRangePicker({ rangeDays, onRangeChange }: DateRangePickerProps) {
  return (
    <Tabs value={String(rangeDays)} onValueChange={(v) => onRangeChange(Number(v))}>
      <TabsList className="h-8">
        {RANGES.map((r) => (
          <TabsTrigger key={r.value} value={String(r.value)} className="px-3 text-xs">
            {r.label}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
