"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useExpertBusinessTypesCatalog } from "@/features/brand-studio/hooks/use-expert-business-types-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";

import { BusinessTypeOnboardingDialog } from "./BusinessTypeOnboardingDialog";

/**
 * Settings-page section that shows the tenant's declared business types
 * with an edit button. Meant to plug into the Brand Studio identity
 * surface so the user can revisit the decision captured during
 * onboarding.
 */
export function BusinessTypesSection() {
  const [editing, setEditing] = useState(false);
  const { settings } = useBrandSettings();
  const { data: catalog } = useExpertBusinessTypesCatalog();
  const declared = settings?.identity?.business_types ?? [];

  const selectedMetadata = declared
    .map((type) => catalog?.business_types.find((t) => t.business_type === type))
    .filter((meta): meta is NonNullable<typeof meta> => Boolean(meta));

  return (
    <>
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle>Tipo de negocio</CardTitle>
            <CardDescription>
              Drive las ofertas que te mostramos en el wizard. Actualiza si tu mix cambia.
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
            <Pencil className="mr-2 h-3 w-3" />
            Editar
          </Button>
        </CardHeader>
        <CardContent>
          {declared.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Aún no has declarado tu tipo de negocio. El wizard está mostrando todos los formatos
              por defecto.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {selectedMetadata.map((meta) => {
                const Icon = resolveIconByName(meta.icon_name);
                return (
                  <Badge
                    key={meta.business_type}
                    variant="secondary"
                    className="text-xs gap-1.5 py-1.5 px-3"
                  >
                    <Icon className="h-3 w-3" />
                    {meta.label_es}
                  </Badge>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <BusinessTypeOnboardingDialog open={editing} onOpenChange={setEditing} />
    </>
  );
}
