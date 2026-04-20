"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";

import { InstancePicker, type InstancePickerInstance } from "@/components/form-runtime";

import { useTestimonials } from "../hooks/use-testimonials";

export interface TestimonialInstancePickerProps {
  tenantId: string;
  activeTestimonialId: string | null;
}

/**
 * Column 2 of the Finder layout for the testimonials section. Lists every
 * testimonial for the current tenant, lets the user pick one (navigates to
 * ``/{tenantId}/brand-studio/testimonials/instance/{id}``) or create a new one.
 */
export function TestimonialInstancePicker({
  tenantId,
  activeTestimonialId,
}: TestimonialInstancePickerProps) {
  const router = useRouter();
  const { testimonials, create, isCreating } = useTestimonials();

  const instances = useMemo<InstancePickerInstance[]>(
    () =>
      testimonials.map((t) => {
        // Lightweight completion score: filled non-author fields / total.
        const fields = [t.content, t.author_role, t.rating, t.source_url, t.author_avatar_url];
        const filled = fields.filter((v) => v !== null && v !== undefined && v !== "").length;
        return {
          id: t.id,
          primary: t.author_name || "Sin autor",
          secondary: t.author_role || (t.media_type !== "text" ? t.media_type : "Texto"),
          completion: filled / fields.length,
        };
      }),
    [testimonials],
  );

  const handleCreate = useCallback(async () => {
    if (isCreating) return;
    const testimonial = await create({ author_name: "Nuevo testimonio" });
    if (testimonial?.id) {
      router.push(`/${tenantId}/brand-studio/testimonials/instance/${testimonial.id}`);
    }
  }, [create, isCreating, router, tenantId]);

  return (
    <InstancePicker
      title="Testimonios"
      createLabel={isCreating ? "Creando…" : "Crear nuevo testimonio"}
      onCreate={handleCreate}
      activeInstanceId={activeTestimonialId}
      instances={instances}
      getInstanceHref={(id) => `/${tenantId}/brand-studio/testimonials/instance/${id}`}
    />
  );
}
