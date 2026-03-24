"use client";

import { useState } from "react";
import { CreativeConcept } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Save, Loader2, ArrowLeft } from "lucide-react";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

interface ConceptFormProps {
    concept: CreativeConcept;
    onSave: (c: CreativeConcept) => Promise<void>;
    onCancel: () => void;
    isSaving: boolean;
}

export function ConceptForm({ concept, onSave, onCancel, isSaving }: ConceptFormProps) {
    const [current, setCurrent] = useState<CreativeConcept>(concept);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSave(current);
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex items-center gap-2 mb-4">
                <button type="button" onClick={onCancel} className="text-muted-foreground hover:text-foreground transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                </button>
                <h3 className="text-sm font-semibold">
                    {concept.name ? "Editar Concepto Creativo" : "Nuevo Concepto Creativo"}
                </h3>
            </div>

            <div className="grid gap-4">
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right text-sm">Nombre</Label>
                    <Input
                        value={current.name || ""}
                        onChange={(e) => setCurrent({ ...current, name: e.target.value })}
                        className="col-span-3"
                        placeholder="Ej: Campaña de Lanzamiento Q2"
                        required
                    />
                </div>
                <div className="grid grid-cols-4 items-start gap-4">
                    <Label className="text-right text-sm pt-2">Descripción</Label>
                    <WithCopilot fieldId="concept_description" fieldLabel="Descripción del Concepto" getValue={() => current.description || ""}>
                      <Textarea
                          value={current.description || ""}
                          onChange={(e) => setCurrent({ ...current, description: e.target.value })}
                          className="col-span-3"
                          placeholder="Describe el concepto creativo, su propósito y contexto..."
                          rows={4}
                      />
                    </WithCopilot>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                    <Label className="text-right text-sm">Tono</Label>
                    <Input
                        value={current.tone || ""}
                        onChange={(e) => setCurrent({ ...current, tone: e.target.value })}
                        className="col-span-3"
                        placeholder="Ej: Inspirador, cercano, educativo"
                    />
                </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
                    Cancelar
                </Button>
                <Button type="submit" disabled={isSaving || !current.name}>
                    {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    Guardar
                </Button>
            </div>
        </form>
    );
}
