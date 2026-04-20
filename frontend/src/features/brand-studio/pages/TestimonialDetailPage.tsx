"use client";

import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import { TestimonialInstancePicker } from "@/features/brand-studio/components/TestimonialInstancePicker";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { useTestimonial } from "@/features/brand-studio/hooks/use-testimonial";
import { testimonialItemSchema } from "@/features/brand-studio/schemas/testimonial-item.schema";
import { testimonialApi, type Testimonial, type TestimonialUpdateDTO } from "@/lib/api/testimonial";

const EDITABLE_FIELDS = [
  "author_name",
  "author_role",
  "author_avatar_url",
  "content",
  "media_type",
  "media_url",
  "rating",
  "source_url",
  "captured_at",
  "language",
  "tags",
  "is_active",
] as const satisfies readonly (keyof TestimonialUpdateDTO)[];

function toEditable(t: Testimonial | null): TestimonialUpdateDTO {
  if (!t) return {};
  const patch: TestimonialUpdateDTO = {};
  for (const key of EDITABLE_FIELDS) {
    const v = t[key];
    if (v !== null && v !== undefined) (patch as Record<string, unknown>)[key] = v;
  }
  return patch;
}

/**
 * Testimonial editor inside the Finder 4-column layout:
 *   Col 1 (layout.tsx) · sections rail
 *   Col 2 (instanceColumn) · TestimonialInstancePicker
 *   Col 3 + 4 · testimonial schema fields + active-field editor
 *
 * Route: /{tenantId}/brand-studio/testimonials/instance/{id}/{fieldId?}
 */
export function TestimonialDetailPage() {
  const params = useParams<{ tenantId?: string; instanceId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const instanceId = params?.instanceId ?? "";

  const { data: testimonial, isLoading } = useTestimonial(instanceId);
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting(
    `testimonials/instance/${instanceId}`,
  );

  const values = useMemo(() => toEditable(testimonial ?? null), [testimonial]);

  const save = useCallback(
    async (patch: TestimonialUpdateDTO) => {
      const token = await getToken();
      if (!token || !instanceId) return;
      await testimonialApi.patch(token, instanceId, patch);
      await queryClient.invalidateQueries({ queryKey: ["testimonials", tenantId] });
      await queryClient.invalidateQueries({
        queryKey: ["testimonial", tenantId, instanceId],
      });
    },
    [getToken, instanceId, queryClient, tenantId],
  );

  if (!instanceId) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No se especificó el identificador del testimonio.
      </div>
    );
  }

  if (!isLoading && !testimonial) {
    return <div className="p-4 text-sm text-muted-foreground">Testimonio no encontrado</div>;
  }

  return (
    <UniversalEditableSection<TestimonialUpdateDTO>
      schema={testimonialItemSchema}
      values={values}
      isLoading={isLoading}
      onSave={save}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      instanceColumn={
        <TestimonialInstancePicker tenantId={tenantId} activeTestimonialId={instanceId} />
      }
    />
  );
}
