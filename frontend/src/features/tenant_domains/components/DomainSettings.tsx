"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

import { useDomains } from "../hooks/useDomains";

import { CustomDomainWizard } from "./CustomDomainWizard";
import { DomainList } from "./DomainList";
import { PlatformSubdomain } from "./PlatformSubdomain";

interface DomainSettingsProps {
  tenantSlug: string;
}

export function DomainSettings({ tenantSlug }: DomainSettingsProps) {
  const [wizardOpen, setWizardOpen] = useState(false);
  const { data: domains, isLoading } = useDomains();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold">Dominios</h2>
        <p className="text-sm text-muted-foreground">
          Gestiona los dominios asociados a tu cuenta.
        </p>
      </div>

      <PlatformSubdomain tenantSlug={tenantSlug} />

      <Separator />

      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">Dominios personalizados</h3>
          <Button size="sm" className="gap-1.5" onClick={() => setWizardOpen(true)}>
            <Plus className="h-4 w-4" />
            Añadir dominio
          </Button>
        </div>

        <DomainList domains={domains ?? []} isLoading={isLoading} />
      </div>

      <CustomDomainWizard open={wizardOpen} onOpenChange={setWizardOpen} />
    </div>
  );
}
