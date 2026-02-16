"use client";

import { Suspense } from "react";
import { SalesDashboard } from "@/features/sales/components/sales-dashboard";

export default function SalesPage() {
  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <Suspense fallback={<div>Cargando Sales Studio...</div>}>
        <SalesDashboard />
      </Suspense>
    </div>
  );
}
