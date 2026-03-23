"use client";

import { useState } from "react";
import { useBrandSettings } from "../../hooks/useBrandSettings";
import { ConceptForm } from "./concept-form";
import { AssetItemForm } from "./asset-item-form";
import { CreativeConcept, FunnelAsset } from "@/features/brand/types";
import { Loader2 } from "lucide-react";

export function AssetsManager() {
    const { settings, saving, updateCommunicationAssets } = useBrandSettings();
    const [editingConcept, setEditingConcept] = useState<CreativeConcept | null>(null);
    const [editingAsset, setEditingAsset] = useState<FunnelAsset | null>(null);

    if (!settings) {
        return (
            <div className="flex justify-center p-8">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
        );
    }

    const commAssets = settings.communication_assets ?? { creative_concepts: [], assets: [], custom_asset_types: [] };

    const handleSaveConcept = async (concept: CreativeConcept) => {
        const concepts = [...commAssets.creative_concepts];
        const idx = concepts.findIndex(c => c.id === concept.id);
        if (idx >= 0) concepts[idx] = concept;
        else concepts.push(concept);
        await updateCommunicationAssets({ ...commAssets, creative_concepts: concepts });
        setEditingConcept(null);
    };

    const handleSaveAsset = async (asset: FunnelAsset) => {
        const assets = [...commAssets.assets];
        const idx = assets.findIndex(a => a.id === asset.id);
        if (idx >= 0) assets[idx] = asset;
        else assets.push(asset);
        await updateCommunicationAssets({ ...commAssets, assets });
        setEditingAsset(null);
    };

    const handleDeleteConcept = async (id: string) => {
        const concepts = commAssets.creative_concepts.filter(c => c.id !== id);
        await updateCommunicationAssets({ ...commAssets, creative_concepts: concepts });
    };

    const handleDeleteAsset = async (id: string) => {
        const assets = commAssets.assets.filter(a => a.id !== id);
        await updateCommunicationAssets({ ...commAssets, assets });
    };

    if (editingConcept) {
        return (
            <ConceptForm
                concept={editingConcept}
                onSave={handleSaveConcept}
                onCancel={() => setEditingConcept(null)}
                isSaving={saving}
            />
        );
    }

    if (editingAsset) {
        return (
            <AssetItemForm
                asset={editingAsset}
                concepts={commAssets.creative_concepts}
                customTypes={commAssets.custom_asset_types}
                onSave={handleSaveAsset}
                onCancel={() => setEditingAsset(null)}
                isSaving={saving}
            />
        );
    }

    return (
        <div className="space-y-6">
            {/* Creative Concepts */}
            <div>
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-sm">Conceptos Creativos</h3>
                    <button
                        onClick={() => setEditingConcept({ id: crypto.randomUUID(), name: "", description: "", tone: "" })}
                        className="text-xs text-primary hover:underline"
                    >
                        + Agregar
                    </button>
                </div>
                {commAssets.creative_concepts.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Sin conceptos creativos aun.</p>
                ) : (
                    <div className="space-y-2">
                        {commAssets.creative_concepts.map(c => (
                            <div key={c.id} className="flex items-start justify-between p-3 border rounded-lg">
                                <div>
                                    <p className="font-medium text-sm">{c.name || "Sin nombre"}</p>
                                    <p className="text-xs text-muted-foreground">{c.tone}</p>
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => setEditingConcept(c)} className="text-xs text-primary hover:underline">
                                        Editar
                                    </button>
                                    <button onClick={() => handleDeleteConcept(c.id)} className="text-xs text-destructive hover:underline">
                                        Eliminar
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Assets grouped by funnel stage */}
            <div>
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-sm">Activos de Comunicacion</h3>
                    <button
                        onClick={() => setEditingAsset({
                            id: crypto.randomUUID(),
                            funnel_stage: "TOFU",
                            asset_type: "",
                            title: "",
                            idea: "",
                            copy_draft: "",
                            objective: "Awareness",
                            status: "draft",
                        })}
                        className="text-xs text-primary hover:underline"
                    >
                        + Agregar
                    </button>
                </div>
                {commAssets.assets.length === 0 ? (
                    <p className="text-sm text-muted-foreground">Sin activos de comunicacion aun.</p>
                ) : (
                    ["TOFU", "MOFU", "BOFU", "retention"].map(stage => {
                        const stageAssets = commAssets.assets.filter(a => a.funnel_stage === stage);
                        if (stageAssets.length === 0) return null;
                        return (
                            <div key={stage} className="mb-4">
                                <h4 className="text-xs font-semibold uppercase text-muted-foreground mb-2">{stage}</h4>
                                <div className="space-y-2">
                                    {stageAssets.map(a => (
                                        <div key={a.id} className="flex items-start justify-between p-3 border rounded-lg">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-xs bg-muted px-1.5 py-0.5 rounded">{a.asset_type}</span>
                                                    <p className="font-medium text-sm">{a.title || "Sin titulo"}</p>
                                                </div>
                                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{a.idea}</p>
                                            </div>
                                            <div className="flex gap-2 shrink-0">
                                                <button onClick={() => setEditingAsset(a)} className="text-xs text-primary hover:underline">
                                                    Editar
                                                </button>
                                                <button onClick={() => handleDeleteAsset(a.id)} className="text-xs text-destructive hover:underline">
                                                    Eliminar
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
