"use client";

import { Save, Loader2, ArrowLeft } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import type { FunnelAsset, CreativeConcept } from "@/features/brand/types";

interface AssetItemFormProps {
  asset: FunnelAsset;
  concepts: CreativeConcept[];
  customTypes: string[];
  onSave: (a: FunnelAsset) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
}

const COMMON_ASSET_TYPES = [
  "reel",
  "carousel",
  "email",
  "blog",
  "webinar",
  "caso_exito",
  "landing",
];

const FUNNEL_STAGES = [
  { value: "TOFU", label: "TOFU (Top of Funnel)" },
  { value: "MOFU", label: "MOFU (Middle of Funnel)" },
  { value: "BOFU", label: "BOFU (Bottom of Funnel)" },
  { value: "retention", label: "Retención" },
];

const OBJECTIVES = [
  { value: "Awareness", label: "Awareness" },
  { value: "Engagement", label: "Engagement" },
  { value: "Conversion", label: "Conversión" },
  { value: "Retention", label: "Retención" },
];

const STATUSES = [
  { value: "draft", label: "Borrador" },
  { value: "approved", label: "Aprobado" },
  { value: "produced", label: "Producido" },
];

export function AssetItemForm({
  asset,
  concepts,
  customTypes,
  onSave,
  onCancel,
  isSaving,
}: AssetItemFormProps) {
  const [current, setCurrent] = useState<FunnelAsset>(asset);

  const allSuggestions = Array.from(new Set([...COMMON_ASSET_TYPES, ...customTypes]));
  const datalistId = `asset-types-${asset.id}`;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSave(current);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <button
          type="button"
          onClick={onCancel}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </button>
        <h3 className="text-sm font-semibold">
          {asset.title ? "Editar Activo" : "Nuevo Activo de Comunicación"}
        </h3>
      </div>

      <div className="grid gap-4">
        {/* Funnel Stage */}
        <div className="grid grid-cols-4 items-center gap-4">
          <Label className="text-right text-sm">Etapa Funnel</Label>
          <Select
            value={current.funnel_stage || "TOFU"}
            onValueChange={(val) => setCurrent({ ...current, funnel_stage: val })}
          >
            <SelectTrigger className="col-span-3">
              <SelectValue placeholder="Selecciona etapa" />
            </SelectTrigger>
            <SelectContent>
              {FUNNEL_STAGES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Asset Type */}
        <div className="grid grid-cols-4 items-center gap-4">
          <Label className="text-right text-sm">Tipo</Label>
          <div className="col-span-3">
            <Input
              value={current.asset_type || ""}
              onChange={(e) => setCurrent({ ...current, asset_type: e.target.value })}
              list={datalistId}
              placeholder="Ej: reel, carousel, email..."
              required
            />
            <datalist id={datalistId}>
              {allSuggestions.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </div>
        </div>

        {/* Title */}
        <div className="grid grid-cols-4 items-center gap-4">
          <Label className="text-right text-sm">Título</Label>
          <Input
            value={current.title || ""}
            onChange={(e) => setCurrent({ ...current, title: e.target.value })}
            className="col-span-3"
            placeholder="Título del activo"
            required
          />
        </div>

        {/* Idea */}
        <div className="grid grid-cols-4 items-start gap-4">
          <Label className="text-right text-sm pt-2">Idea</Label>
          <Textarea
            value={current.idea || ""}
            onChange={(e) => setCurrent({ ...current, idea: e.target.value })}
            className="col-span-3"
            placeholder="Describe la idea principal del activo..."
            rows={3}
          />
        </div>

        {/* Copy Draft */}
        <div className="grid grid-cols-4 items-start gap-4">
          <Label className="text-right text-sm pt-2">Copy (Borrador)</Label>
          <Textarea
            value={current.copy_draft || ""}
            onChange={(e) => setCurrent({ ...current, copy_draft: e.target.value })}
            className="col-span-3"
            placeholder="Borrador del copy o guión..."
            rows={4}
          />
        </div>

        {/* Objective */}
        <div className="grid grid-cols-4 items-center gap-4">
          <Label className="text-right text-sm">Objetivo</Label>
          <Select
            value={current.objective || "Awareness"}
            onValueChange={(val) => setCurrent({ ...current, objective: val })}
          >
            <SelectTrigger className="col-span-3">
              <SelectValue placeholder="Selecciona objetivo" />
            </SelectTrigger>
            <SelectContent>
              {OBJECTIVES.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Concept */}
        {concepts.length > 0 && (
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right text-sm">Concepto</Label>
            <Select
              value={current.concept_id || "_none"}
              onValueChange={(val) =>
                setCurrent({ ...current, concept_id: val === "_none" ? undefined : val })
              }
            >
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Sin concepto asignado" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="_none">Sin concepto</SelectItem>
                {concepts.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name || "Sin nombre"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Status */}
        <div className="grid grid-cols-4 items-center gap-4">
          <Label className="text-right text-sm">Estado</Label>
          <Select
            value={current.status || "draft"}
            onValueChange={(val) => setCurrent({ ...current, status: val })}
          >
            <SelectTrigger className="col-span-3">
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              {STATUSES.map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isSaving || !current.asset_type || !current.title}>
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar
        </Button>
      </div>
    </form>
  );
}
