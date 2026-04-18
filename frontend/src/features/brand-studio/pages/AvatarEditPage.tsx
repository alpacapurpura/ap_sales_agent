"use client";

import { useParams } from "next/navigation";

import "@/features/brand-studio/actions/registry";

/**
 * Avatar edit route. Sprint 1 stub — Sprint 2 replaces with the ported
 * avatar-form rich action (creates sub-entity via the avatar API).
 */
export function AvatarEditPage() {
  const params = useParams<{ id: string; tenantId: string }>();
  const id = params?.id ?? "";

  return (
    <section className="p-4">
      <h1 className="text-lg font-semibold">Editar avatar</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Avatar id: <code>{id}</code>
      </p>
      <p className="mt-2 text-sm text-muted-foreground">
        Editor detallado pendiente de portar en Sprint 2 (AvatarAction).
      </p>
    </section>
  );
}
