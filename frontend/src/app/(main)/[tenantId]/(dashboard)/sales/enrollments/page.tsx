import { Suspense } from "react";

import { EnrollmentsPage } from "@/features/closer-studio/components/EnrollmentsPage";

export const metadata = {
  title: "Inscripciones · Closer Studio",
};

/**
 *
 */
export default function CloserEnrollmentsPage() {
  return (
    <div className="space-y-6 p-10 pb-16">
      <Suspense fallback={<div>Cargando inscripciones…</div>}>
        <EnrollmentsPage />
      </Suspense>
    </div>
  );
}
