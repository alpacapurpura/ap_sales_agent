"use client";

import { MessageSquareQuote } from "lucide-react";
import { useParams } from "next/navigation";

import { TestimonialInstancePicker } from "@/features/brand-studio/components/TestimonialInstancePicker";

/**
 * Landing view for ``/brand-studio/testimonials`` (no testimonial
 * selected yet). Renders the TestimonialInstancePicker as column 2 and a
 * welcome pane inviting the user to pick or create.
 *
 * Once a testimonial is clicked, the user lands on
 * ``/brand-studio/testimonials/instance/{id}`` → ``TestimonialDetailPage``
 * where the full 4-column Finder layout takes over.
 */
export function TestimonialsLandingPage() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <TestimonialInstancePicker tenantId={tenantId} activeTestimonialId={null} />
      <div className="flex min-h-0 min-w-0 flex-1 items-center justify-center bg-card p-12 text-center">
        <div className="max-w-[420px]">
          <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-brand/15 text-brand">
            <MessageSquareQuote className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="mb-3 text-xl font-semibold text-foreground">Elige o crea un testimonio</h1>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Los testimonios son la voz de tus clientes. Se reutilizan automáticamente en landings,
            ofertas y en lo que responde el Sales Agent — sin duplicar datos.
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Selecciona uno del panel izquierdo o toca{" "}
            <span className="font-medium text-foreground">Crear nuevo testimonio</span>.
          </p>
        </div>
      </div>
    </div>
  );
}
