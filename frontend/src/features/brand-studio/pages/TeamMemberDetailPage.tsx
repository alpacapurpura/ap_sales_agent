"use client";

import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { UniversalEditableSection } from "@/components/form-runtime";
import { TeamMemberInstancePicker } from "@/features/brand-studio/components/TeamMemberInstancePicker";
import { useBrandStudioFieldRouting } from "@/features/brand-studio/hooks/use-field-routing";
import { useTeamMember } from "@/features/brand-studio/hooks/use-team-member";
import { teamMemberItemSchema } from "@/features/brand-studio/schemas/team-member-item.schema";
import { teamMemberApi, type TeamMember, type TeamMemberUpdateDTO } from "@/lib/api/team-member";

const EDITABLE_FIELDS = [
  "name",
  "role",
  "bio",
  "headshot_url",
  "is_primary_voice",
  "gender",
  "communication_style",
  "personal_website",
  "personal_linkedin",
  "personal_instagram",
  "personal_tiktok",
  "personal_facebook",
  "work_whatsapp",
  "gallery",
  "sort_order",
] as const satisfies readonly (keyof TeamMemberUpdateDTO)[];

function toEditable(member: TeamMember | null): TeamMemberUpdateDTO {
  if (!member) return {};
  const patch: TeamMemberUpdateDTO = {};
  for (const key of EDITABLE_FIELDS) {
    const v = member[key];
    if (v !== null && v !== undefined) (patch as Record<string, unknown>)[key] = v;
  }
  return patch;
}

/**
 * TeamMember editor inside the Finder 4-column layout.
 *
 * Route: /{tenantId}/brand-studio/team/instance/{id}/{fieldId?}
 */
export function TeamMemberDetailPage() {
  const params = useParams<{ tenantId?: string; instanceId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const instanceId = params?.instanceId ?? "";

  const { data: member, isLoading } = useTeamMember(instanceId);
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const { activeFieldId, getFieldHref } = useBrandStudioFieldRouting(`team/instance/${instanceId}`);

  const values = useMemo(() => toEditable(member ?? null), [member]);

  const save = useCallback(
    async (patch: TeamMemberUpdateDTO) => {
      const token = await getToken();
      if (!token || !instanceId) return;
      await teamMemberApi.patch(token, instanceId, patch);
      await queryClient.invalidateQueries({ queryKey: ["team_members", tenantId] });
      await queryClient.invalidateQueries({
        queryKey: ["team_member", tenantId, instanceId],
      });
    },
    [getToken, instanceId, queryClient, tenantId],
  );

  if (!instanceId) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No se especificó el identificador del miembro.
      </div>
    );
  }

  if (!isLoading && !member) {
    return <div className="p-4 text-sm text-muted-foreground">Miembro no encontrado</div>;
  }

  return (
    <UniversalEditableSection<TeamMemberUpdateDTO>
      schema={teamMemberItemSchema}
      values={values}
      isLoading={isLoading}
      onSave={save}
      activeFieldId={activeFieldId}
      getFieldHref={getFieldHref}
      instanceColumn={<TeamMemberInstancePicker tenantId={tenantId} activeMemberId={instanceId} />}
    />
  );
}
