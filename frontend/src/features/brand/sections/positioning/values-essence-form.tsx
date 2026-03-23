"use client";

import { useState, useEffect } from "react";
import { BrandPositioning, BrandValues, ReasonToBelieve } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Save, Loader2 } from "lucide-react";
import { Trash2 } from "lucide-react";
import { RtbItemForm } from "./rtb-item-form";

interface ValuesEssenceFormProps {
  positioning: BrandPositioning;
  onSave: (data: BrandPositioning) => Promise<void>;
  isSaving: boolean;
}

const ARCHETYPE_OPTIONS = [
  "El Inocente",
  "El Explorador",
  "El Sabio",
  "El Héroe",
  "El Rebelde",
  "El Mago",
  "El Amante",
  "El Bufón",
  "El Cuidador",
  "El Creador",
  "El Gobernante",
  "El Hombre Común",
];

export function ValuesEssenceForm({ positioning, onSave, isSaving }: ValuesEssenceFormProps) {
  const [data, setData] = useState<BrandPositioning>(positioning);

  useEffect(() => {
    setData(positioning);
  }, [positioning]);

  const values: BrandValues = data.values ?? {
    core_values: [],
    personality_traits: [],
    archetype: "",
  };
  const rtbs = data.reasons_to_believe ?? [];

  const updateValues = (partial: Partial<BrandValues>) => {
    setData({ ...data, values: { ...values, ...partial } });
  };

  // --- Core Values ---
  const addCoreValue = () => {
    updateValues({ core_values: [...values.core_values, ""] });
  };

  const updateCoreValue = (index: number, value: string) => {
    const updated = [...values.core_values];
    updated[index] = value;
    updateValues({ core_values: updated });
  };

  const removeCoreValue = (index: number) => {
    updateValues({ core_values: values.core_values.filter((_, i) => i !== index) });
  };

  // --- Personality Traits ---
  const addTrait = () => {
    updateValues({ personality_traits: [...values.personality_traits, ""] });
  };

  const updateTrait = (index: number, value: string) => {
    const updated = [...values.personality_traits];
    updated[index] = value;
    updateValues({ personality_traits: updated });
  };

  const removeTrait = (index: number) => {
    updateValues({ personality_traits: values.personality_traits.filter((_, i) => i !== index) });
  };

  // --- RTBs ---
  const addRtb = () => {
    setData({
      ...data,
      reasons_to_believe: [
        ...rtbs,
        { id: crypto.randomUUID(), type: "", statement: "", proof_url: "" },
      ],
    });
  };

  const updateRtb = (index: number, rtb: ReasonToBelieve) => {
    const updated = [...rtbs];
    updated[index] = rtb;
    setData({ ...data, reasons_to_believe: updated });
  };

  const removeRtb = (index: number) => {
    setData({ ...data, reasons_to_believe: rtbs.filter((_, i) => i !== index) });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Core Values */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Valores Centrales</Label>
          <Button type="button" variant="outline" size="sm" onClick={addCoreValue}>
            <Plus className="w-4 h-4 mr-2" />
            Agregar
          </Button>
        </div>
        {values.core_values.map((v, i) => (
          <div key={i} className="flex gap-2 items-center">
            <Input
              value={v}
              onChange={(e) => updateCoreValue(i, e.target.value)}
              placeholder="Ej: Transparencia, Innovación..."
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-destructive h-8 w-8 flex-shrink-0"
              onClick={() => removeCoreValue(i)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        ))}
        {values.core_values.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-2 italic">
            Sin valores registrados.
          </p>
        )}
      </div>

      {/* Personality Traits */}
      <div className="space-y-3 border-t pt-6">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Rasgos de Personalidad</Label>
          <Button type="button" variant="outline" size="sm" onClick={addTrait}>
            <Plus className="w-4 h-4 mr-2" />
            Agregar
          </Button>
        </div>
        {values.personality_traits.map((t, i) => (
          <div key={i} className="flex gap-2 items-center">
            <Input
              value={t}
              onChange={(e) => updateTrait(i, e.target.value)}
              placeholder="Ej: Cercano, Experto, Audaz..."
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-muted-foreground hover:text-destructive h-8 w-8 flex-shrink-0"
              onClick={() => removeTrait(i)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        ))}
        {values.personality_traits.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-2 italic">
            Sin rasgos registrados.
          </p>
        )}
      </div>

      {/* Archetype */}
      <div className="space-y-2 border-t pt-6">
        <Label className="text-base font-semibold">Arquetipo de Marca</Label>
        <Select
          value={values.archetype || ""}
          onValueChange={(val) => updateValues({ archetype: val })}
        >
          <SelectTrigger className="w-full md:w-64">
            <SelectValue placeholder="Seleccionar arquetipo..." />
          </SelectTrigger>
          <SelectContent>
            {ARCHETYPE_OPTIONS.map((a) => (
              <SelectItem key={a} value={a}>{a}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          El arquetipo define la personalidad narrativa de tu marca.
        </p>
      </div>

      {/* Reasons to Believe */}
      <div className="space-y-4 border-t pt-6">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Razones para Creer (RTBs)</Label>
          <Button type="button" variant="outline" size="sm" onClick={addRtb}>
            <Plus className="w-4 h-4 mr-2" />
            Agregar
          </Button>
        </div>
        <div className="space-y-3">
          {rtbs.map((rtb, i) => (
            <RtbItemForm
              key={rtb.id}
              rtb={rtb}
              onChange={(updated) => updateRtb(i, updated)}
              onRemove={() => removeRtb(i)}
            />
          ))}
          {rtbs.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4 italic">
              Sin razones para creer. Agrega datos, casos de éxito o certificaciones que respalden tu marca.
            </p>
          )}
        </div>
      </div>

      {/* Discriminator */}
      <div className="space-y-2 border-t pt-6">
        <Label htmlFor="discriminator" className="text-base font-semibold">Discriminador</Label>
        <Textarea
          id="discriminator"
          value={data.discriminator || ""}
          onChange={(e) => setData({ ...data, discriminator: e.target.value })}
          placeholder="La razón principal por la que un cliente te elige a ti sobre la competencia..."
          className="min-h-[80px]"
        />
        <p className="text-xs text-muted-foreground">
          El factor decisivo que te hace diferente e irremplazable.
        </p>
      </div>

      {/* Brand Essence */}
      <div className="space-y-2 border-t pt-6">
        <Label htmlFor="brand_essence" className="text-base font-semibold">Esencia de Marca</Label>
        <Input
          id="brand_essence"
          value={data.brand_essence || ""}
          onChange={(e) => setData({ ...data, brand_essence: e.target.value })}
          placeholder="Ej: Empoderar al experto"
          className="text-lg font-medium"
        />
        <p className="text-xs text-muted-foreground">
          Una frase corta (2-4 palabras) que captura el alma de tu marca.
        </p>
      </div>

      {/* Submit */}
      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar Valores y Esencia
        </Button>
      </div>
    </form>
  );
}
