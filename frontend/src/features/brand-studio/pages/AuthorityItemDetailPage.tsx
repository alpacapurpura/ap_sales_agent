"use client";

import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import { AuthorityItemInstancePicker } from "@/features/brand-studio/components/AuthorityItemInstancePicker";
import { useAuthorityItem } from "@/features/brand-studio/hooks/use-authority-item";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { authorityItemSchema } from "@/features/brand-studio/schemas/authority-item.schema";
import {
  authorityApi,
  type AuthorityItem,
  type AuthorityUpdateDTO,
} from "@/lib/api/authority-item";

const EDITABLE_FIELDS = [
  "entity_name",
  "authority_type",
  "context",
  "proof_url",
  "logo_url",
  "obtained_at",
  "expires_at",
  "is_active",
] as const satisfies readonly (keyof AuthorityUpdateDTO)[];

function toEditable(item: AuthorityItem | null): AuthorityUpdateDTO {
  if (!item) return {};
  const patch: AuthorityUpdateDTO = {};
  for (const key of EDITABLE_FIELDS) {
    const v = item[key];
    if (v !== null && v !== undefined) (patch as Record<string, unknown>)[key] = v;
  }
  return patch;
}

/**
 * AuthorityItem editor inside the Finder 4-column layout.
 *
 * Route: /{tenantId}/brand-studio/authority/instance/{id}/{fieldId?}
 */
export function AuthorityItemDetailPage() {
  const params = useParams<{ tenantId?: string; instanceId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const instanceId = params?.instanceId ?? "";

  const { data: item, isLoading } = useAuthorityItem(instanceId);
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting(
    `authority/instance/${instanceId}`,
  );

  const values = useMemo(() => toEditable(item ?? null), [item]);

  const save = useCallback(
    async (patch: AuthorityUpdateDTO) => {
      const token = await getToken();
      if (!token || !instanceId) return;
      await authorityApi.patch(token, instanceId, patch);
      await queryClient.invalidateQueries({ queryKey: ["authority_items", tenantId] });
      await queryClient.invalidateQueries({
        queryKey: ["authority_item", tenantId, instanceId],
      });
    },
    [getToken, instanceId, queryClient, tenantId],
  );

  if (!instanceId) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No se especificó el identificador del ítem.
      </div>
    );
  }

  if (!isLoading && !item) {
    return (
      <div className="p-4 text-sm text-muted-foreground">Señal de autoridad no encontrada</div>
    );
  }

  return (
    <UniversalEditableSection<AuthorityUpdateDTO>
      schema={authorityItemSchema}
      values={values}
      isLoading={isLoading}
      onSave={save}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      instanceColumn={<AuthorityItemInstancePicker tenantId={tenantId} activeItemId={instanceId} />}
    />
  );
}
