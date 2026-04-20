"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";

import { InstancePicker, type InstancePickerInstance } from "@/components/form-runtime";

import { useAuthorityItems } from "../hooks/use-authority-items";

const TYPE_LABELS: Record<string, string> = {
  certification: "Certificación",
  award: "Premio",
  media_mention: "Mención en medios",
  published_work: "Publicación",
  client_logo: "Cliente destacado",
  credential: "Credencial",
  partnership: "Alianza",
  speaking: "Ponencia",
  podcast: "Podcast",
  other: "Otro",
};

export interface AuthorityItemInstancePickerProps {
  tenantId: string;
  activeItemId: string | null;
}

/**
 * Column 2 of the Finder layout for the authority section. Lists every
 * authority item for the current tenant, lets the user pick one or create
 * a new one.
 */
export function AuthorityItemInstancePicker({
  tenantId,
  activeItemId,
}: AuthorityItemInstancePickerProps) {
  const router = useRouter();
  const { authorityItems, create, isCreating } = useAuthorityItems();

  const instances = useMemo<InstancePickerInstance[]>(
    () =>
      authorityItems.map((item) => {
        const fields = [item.context, item.proof_url, item.logo_url, item.obtained_at];
        const filled = fields.filter((v) => v !== null && v !== undefined && v !== "").length;
        return {
          id: item.id,
          primary: item.entity_name || "Sin nombre",
          secondary: TYPE_LABELS[item.authority_type] ?? item.authority_type,
          completion: filled / fields.length,
        };
      }),
    [authorityItems],
  );

  const handleCreate = useCallback(async () => {
    if (isCreating) return;
    const item = await create({
      entity_name: "Nueva señal",
      authority_type: "other",
    });
    if (item?.id) {
      router.push(`/${tenantId}/brand-studio/authority/instance/${item.id}`);
    }
  }, [create, isCreating, router, tenantId]);

  return (
    <InstancePicker
      title="Autoridad"
      createLabel={isCreating ? "Creando…" : "Agregar señal de autoridad"}
      onCreate={handleCreate}
      activeInstanceId={activeItemId}
      instances={instances}
      getInstanceHref={(id) => `/${tenantId}/brand-studio/authority/instance/${id}`}
    />
  );
}
