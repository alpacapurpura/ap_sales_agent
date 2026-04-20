"use client";

import { useRouter } from "next/navigation";
import { useCallback, useMemo } from "react";

import { InstancePicker, type InstancePickerInstance } from "@/components/form-runtime";

import { useTeamMembers } from "../hooks/use-team-members";

export interface TeamMemberInstancePickerProps {
  tenantId: string;
  activeMemberId: string | null;
}

/**
 * Column 2 of the Finder layout for the team section. Lists every team
 * member for the current tenant, lets the user pick one or create a new one.
 */
export function TeamMemberInstancePicker({
  tenantId,
  activeMemberId,
}: TeamMemberInstancePickerProps) {
  const router = useRouter();
  const { teamMembers, create, isCreating } = useTeamMembers();

  const instances = useMemo<InstancePickerInstance[]>(
    () =>
      teamMembers.map((m) => {
        const fields = [m.role, m.bio, m.headshot_url, m.communication_style];
        const filled = fields.filter((v) => v !== null && v !== undefined && v !== "").length;
        return {
          id: m.id,
          primary: m.name || "Sin nombre",
          secondary: m.role || (m.is_primary_voice ? "Voz principal" : "Miembro"),
          completion: filled / fields.length,
        };
      }),
    [teamMembers],
  );

  const handleCreate = useCallback(async () => {
    if (isCreating) return;
    const member = await create({ name: "Nuevo miembro" });
    if (member?.id) {
      router.push(`/${tenantId}/brand-studio/team/instance/${member.id}`);
    }
  }, [create, isCreating, router, tenantId]);

  return (
    <InstancePicker
      title="Equipo"
      createLabel={isCreating ? "Creando…" : "Agregar miembro al equipo"}
      onCreate={handleCreate}
      activeInstanceId={activeMemberId}
      instances={instances}
      getInstanceHref={(id) => `/${tenantId}/brand-studio/team/instance/${id}`}
    />
  );
}
