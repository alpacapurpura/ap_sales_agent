"use client";

import { CommunicationAssets } from "@/features/brand/types";
import { Badge } from "@/components/ui/badge";
import { Megaphone, Lightbulb, Plus, PencilLine } from "lucide-react";

interface AssetsPreviewProps {
  communicationAssets: CommunicationAssets;
  onEdit: () => void;
}

const STAGE_LABELS: Record<string, string> = {
  TOFU: "TOFU",
  MOFU: "MOFU",
  BOFU: "BOFU",
  retention: "Retención",
};

const STAGE_COLORS: Record<string, string> = {
  TOFU: "bg-blue-500/10 text-blue-600",
  MOFU: "bg-amber-500/10 text-amber-600",
  BOFU: "bg-green-500/10 text-green-600",
  retention: "bg-purple-500/10 text-purple-600",
};

const STATUS_VARIANTS: Record<string, "default" | "secondary" | "outline"> = {
  draft: "outline",
  approved: "secondary",
  produced: "default",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Borrador",
  approved: "Aprobado",
  produced: "Producido",
};

export function AssetsPreview({ communicationAssets, onEdit }: AssetsPreviewProps) {
  const { creative_concepts, assets } = communicationAssets;
  const hasContent = creative_concepts.length > 0 || assets.length > 0;

  return (
    <section className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40">
      {/* Header */}
      <div
        className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors cursor-pointer"
        onClick={onEdit}
      >
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <Megaphone className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Activos de Comunicacion</h3>
        <button className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity text-xs text-primary flex items-center gap-1">
          <PencilLine className="w-3.5 h-3.5" />
          Editar
        </button>
      </div>

      {!hasContent ? (
        <div className="pl-0 md:pl-14 cursor-pointer" onClick={onEdit}>
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Define los conceptos creativos y activos que dan vida a tu marca en cada etapa del
            funnel.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Configurar Activos
          </span>
        </div>
      ) : (
        <div className="pl-0 md:pl-14 space-y-8">
          {/* Creative Concepts Row */}
          {creative_concepts.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-4 h-4 text-muted-foreground" />
                <h4 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider">
                  Conceptos Creativos
                </h4>
              </div>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {creative_concepts.map((concept) => (
                  <div
                    key={concept.id}
                    className="shrink-0 w-56 bg-card border rounded-lg p-4 hover:shadow-md transition-all cursor-pointer"
                    onClick={onEdit}
                  >
                    <p className="font-medium text-sm truncate">{concept.name || "Sin nombre"}</p>
                    {concept.tone && (
                      <p className="text-xs text-muted-foreground mt-1">Tono: {concept.tone}</p>
                    )}
                    {concept.description && (
                      <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
                        {concept.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Funnel Stage Columns */}
          {assets.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {(["TOFU", "MOFU", "BOFU", "retention"] as const).map((stage) => {
                const stageAssets = assets.filter((a) => a.funnel_stage === stage);
                return (
                  <div key={stage} className="space-y-2">
                    <div
                      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold ${STAGE_COLORS[stage] || "bg-muted text-muted-foreground"}`}
                    >
                      {STAGE_LABELS[stage] || stage}
                      {stageAssets.length > 0 && (
                        <span className="ml-1.5 opacity-60">({stageAssets.length})</span>
                      )}
                    </div>
                    {stageAssets.length === 0 ? (
                      <div
                        className="flex flex-col items-center justify-center py-8 border-2 border-dashed border-muted-foreground/20 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors cursor-pointer"
                        onClick={onEdit}
                      >
                        <Plus className="w-4 h-4 text-muted-foreground/40 mb-1" />
                        <span className="text-xs text-muted-foreground">Agregar</span>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {stageAssets.map((asset) => (
                          <div
                            key={asset.id}
                            className="bg-card border rounded-lg p-3 hover:shadow-md transition-all cursor-pointer"
                            onClick={onEdit}
                          >
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <Badge variant="secondary" className="text-[10px] h-5 px-1.5">
                                {asset.asset_type}
                              </Badge>
                              {asset.status && (
                                <Badge
                                  variant={STATUS_VARIANTS[asset.status] || "outline"}
                                  className="text-[10px] h-5 px-1.5"
                                >
                                  {STATUS_LABELS[asset.status] || asset.status}
                                </Badge>
                              )}
                            </div>
                            <p className="font-medium text-sm truncate">
                              {asset.title || "Sin titulo"}
                            </p>
                            {asset.objective && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {asset.objective}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
