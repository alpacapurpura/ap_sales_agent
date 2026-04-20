import { Suspense } from "react";

import { SalesDashboard } from "@/features/sales/components/SalesDashboard";

/**
 *
 */
export default function SalesResumenPage() {
  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <Suspense fallback={<div>Cargando Closer Studio...</div>}>
        <SalesDashboard />
      </Suspense>
    </div>
  );
}
