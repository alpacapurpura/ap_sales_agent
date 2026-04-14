"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Rocket, Plus, CalendarPlus } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useEditions } from "../../hooks/use-editions";
import {
  LaunchEdition,
  LaunchEditionCreate,
  LaunchEditionUpdate,
  PricingStructure,
} from "../../types";
import { EditionCard } from "./EditionCard";
import { EditionFormDialog } from "./EditionFormDialog";

interface EditionsSectionProps {
  offerId: string;
  offerPricing: PricingStructure[];
  currency: string;
}

export function EditionsSection({ offerId, offerPricing, currency }: EditionsSectionProps) {
  const { editions, loading, createEdition, updateEdition, deleteEdition, duplicateEdition } =
    useEditions(offerId);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEdition, setEditingEdition] = useState<LaunchEdition | undefined>();

  const handleCreate = () => {
    setEditingEdition(undefined);
    setDialogOpen(true);
  };

  const handleEdit = (edition: LaunchEdition) => {
    setEditingEdition(edition);
    setDialogOpen(true);
  };

  const handleSave = async (data: LaunchEditionCreate | LaunchEditionUpdate) => {
    if (editingEdition) {
      await updateEdition({ editionId: editingEdition.id, data: data as LaunchEditionUpdate });
    } else {
      await createEdition(data as LaunchEditionCreate);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-4 border-b bg-purple-50/50 dark:bg-purple-950/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-purple-100 dark:bg-purple-900/30">
              <Rocket className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-base">Ediciones de Lanzamiento</CardTitle>
              <CardDescription>
                Cada edición tiene sus propias fechas y opcionalmente precios distintos
              </CardDescription>
            </div>
          </div>
          <Button onClick={handleCreate} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Nueva Edición
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : editions.length === 0 ? (
          <div className="text-center py-12">
            <CalendarPlus className="h-10 w-10 mx-auto text-muted-foreground/30 mb-3" />
            <h3 className="font-semibold text-sm mb-1">Sin ediciones todavía</h3>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto mb-4">
              Crea tu primera edición para definir fechas de lanzamiento y precios específicos.
            </p>
            <Button variant="outline" size="sm" onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-1" />
              Crear Primera Edición
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {editions.map((edition) => (
              <EditionCard
                key={edition.id}
                edition={edition}
                onEdit={() => handleEdit(edition)}
                onDuplicate={() => duplicateEdition(edition.id)}
                onDelete={() => deleteEdition(edition.id)}
              />
            ))}
          </div>
        )}

        <EditionFormDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          edition={editingEdition}
          offerPricing={offerPricing}
          currency={currency}
          onSave={handleSave}
        />
      </CardContent>
    </Card>
  );
}
