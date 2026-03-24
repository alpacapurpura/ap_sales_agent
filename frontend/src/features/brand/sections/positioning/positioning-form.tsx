"use client";

import { useState, useEffect } from "react";
import { BrandPositioning, BrandCompetitor, CompetitiveEnvironment, ConsumerInsight, BrandBenefits } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Trash2, Save, Loader2 } from "lucide-react";

interface PositioningFormProps {
  positioning: BrandPositioning;
  onSave: (data: BrandPositioning) => Promise<void>;
  isSaving: boolean;
}

export function PositioningForm({ positioning, onSave, isSaving }: PositioningFormProps) {
  const [data, setData] = useState<BrandPositioning>(positioning);

  useEffect(() => {
    setData(positioning);
  }, [positioning]);

  const env = data.competitive_environment ?? {
    technical_enemy: "",
    philosophical_enemy: "",
    direct_competitors: [],
    indirect_competitors: [],
  };

  const insight = data.insight ?? { tension: "", observation: "", implication: "" };
  const benefits = data.benefits ?? { functional_benefits: [], emotional_benefits: [] };

  const updateEnv = (partial: Partial<CompetitiveEnvironment>) => {
    setData({ ...data, competitive_environment: { ...env, ...partial } });
  };

  const updateInsight = (partial: Partial<ConsumerInsight>) => {
    setData({ ...data, insight: { ...insight, ...partial } });
  };

  const updateBenefits = (partial: Partial<BrandBenefits>) => {
    setData({ ...data, benefits: { ...benefits, ...partial } });
  };

  // --- Direct Competitors ---
  const addDirectCompetitor = () => {
    updateEnv({
      direct_competitors: [
        ...env.direct_competitors,
        { id: crypto.randomUUID(), name: "", differentiation: "" },
      ],
    });
  };

  const updateDirectCompetitor = (id: string, field: keyof BrandCompetitor, value: string) => {
    updateEnv({
      direct_competitors: env.direct_competitors.map((c) =>
        c.id === id ? { ...c, [field]: value } : c
      ),
    });
  };

  const removeDirectCompetitor = (id: string) => {
    updateEnv({ direct_competitors: env.direct_competitors.filter((c) => c.id !== id) });
  };

  // --- Indirect Competitors ---
  const addIndirectCompetitor = () => {
    updateEnv({
      indirect_competitors: [
        ...env.indirect_competitors,
        { id: crypto.randomUUID(), name: "", differentiation: "" },
      ],
    });
  };

  const updateIndirectCompetitor = (id: string, field: keyof BrandCompetitor, value: string) => {
    updateEnv({
      indirect_competitors: env.indirect_competitors.map((c) =>
        c.id === id ? { ...c, [field]: value } : c
      ),
    });
  };

  const removeIndirectCompetitor = (id: string) => {
    updateEnv({ indirect_competitors: env.indirect_competitors.filter((c) => c.id !== id) });
  };

  // --- Functional Benefits ---
  const addFunctionalBenefit = () => {
    updateBenefits({ functional_benefits: [...benefits.functional_benefits, ""] });
  };

  const updateFunctionalBenefit = (index: number, value: string) => {
    const updated = [...benefits.functional_benefits];
    updated[index] = value;
    updateBenefits({ functional_benefits: updated });
  };

  const removeFunctionalBenefit = (index: number) => {
    updateBenefits({ functional_benefits: benefits.functional_benefits.filter((_, i) => i !== index) });
  };

  // --- Emotional Benefits ---
  const addEmotionalBenefit = () => {
    updateBenefits({ emotional_benefits: [...benefits.emotional_benefits, ""] });
  };

  const updateEmotionalBenefit = (index: number, value: string) => {
    const updated = [...benefits.emotional_benefits];
    updated[index] = value;
    updateBenefits({ emotional_benefits: updated });
  };

  const removeEmotionalBenefit = (index: number) => {
    updateBenefits({ emotional_benefits: benefits.emotional_benefits.filter((_, i) => i !== index) });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* UVP */}
      <div className="space-y-2">
        <Label htmlFor="uvp">Propuesta de Valor Unica (UVP)</Label>
        <Textarea
          id="uvp"
          value={data.unique_value_proposition || ""}
          onChange={(e) => setData({ ...data, unique_value_proposition: e.target.value })}
          placeholder="Que te hace unico y diferente en el mercado? Completa: 'Solo nosotros [capacidad] porque [razon]'"
          className="min-h-[100px]"
        />
        <p className="text-xs text-muted-foreground">Tu promesa defensible. Completa: &apos;Somos los unicos que [X] porque [Y]&apos;</p>
      </div>

      {/* Enemies */}
      <div className="space-y-4">
        <h4 className="text-base font-semibold">Enemigos de Marca</h4>
        <div className="space-y-2">
          <Label htmlFor="technical_enemy">Enemigo Técnico</Label>
          <Textarea
            id="technical_enemy"
            value={env.technical_enemy || ""}
            onChange={(e) => updateEnv({ technical_enemy: e.target.value })}
            placeholder="El problema concreto que tu marca combate (ej: la desinformación, los procesos manuales...)"
            className="min-h-[80px]"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="philosophical_enemy">Enemigo Filosófico</Label>
          <Textarea
            id="philosophical_enemy"
            value={env.philosophical_enemy || ""}
            onChange={(e) => updateEnv({ philosophical_enemy: e.target.value })}
            placeholder="La creencia o sistema contra el que luchas (ej: que el marketing tiene que ser complicado...)"
            className="min-h-[80px]"
          />
        </div>
      </div>

      {/* Direct Competitors */}
      <div className="space-y-4 border-t pt-6">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Competidores Directos</Label>
          <Button type="button" variant="outline" size="sm" onClick={addDirectCompetitor}>
            <Plus className="w-4 h-4 mr-2" />
            Agregar
          </Button>
        </div>
        <div className="space-y-3">
          {env.direct_competitors.map((c) => (
            <div key={c.id} className="flex gap-3 items-start p-3 bg-muted/20 rounded-lg border">
              <div className="flex gap-2 flex-1">
                <Input
                  value={c.name}
                  onChange={(e) => updateDirectCompetitor(c.id, "name", e.target.value)}
                  placeholder="Nombre"
                  className="w-1/3"
                />
                <Input
                  value={c.differentiation || ""}
                  onChange={(e) => updateDirectCompetitor(c.id, "differentiation", e.target.value)}
                  placeholder="Diferenciación vs. ellos"
                  className="flex-1"
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive h-8 w-8"
                onClick={() => removeDirectCompetitor(c.id)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}
          {env.direct_competitors.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4 italic">
              No hay competidores directos registrados.
            </p>
          )}
        </div>
      </div>

      {/* Indirect Competitors */}
      <div className="space-y-4 border-t pt-6">
        <div className="flex items-center justify-between">
          <Label className="text-base font-semibold">Competidores Indirectos</Label>
          <Button type="button" variant="outline" size="sm" onClick={addIndirectCompetitor}>
            <Plus className="w-4 h-4 mr-2" />
            Agregar
          </Button>
        </div>
        <div className="space-y-3">
          {env.indirect_competitors.map((c) => (
            <div key={c.id} className="flex gap-3 items-start p-3 bg-muted/20 rounded-lg border">
              <div className="flex gap-2 flex-1">
                <Input
                  value={c.name}
                  onChange={(e) => updateIndirectCompetitor(c.id, "name", e.target.value)}
                  placeholder="Nombre"
                  className="w-1/3"
                />
                <Input
                  value={c.differentiation || ""}
                  onChange={(e) => updateIndirectCompetitor(c.id, "differentiation", e.target.value)}
                  placeholder="Diferenciación vs. ellos"
                  className="flex-1"
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive h-8 w-8"
                onClick={() => removeIndirectCompetitor(c.id)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}
          {env.indirect_competitors.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4 italic">
              No hay competidores indirectos registrados.
            </p>
          )}
        </div>
      </div>

      {/* Consumer Insight */}
      <div className="space-y-4 border-t pt-6">
        <h4 className="text-base font-semibold">Consumer Insight</h4>
        <div className="space-y-2">
          <Label htmlFor="tension">Tensión</Label>
          <Textarea
            id="tension"
            value={insight.tension || ""}
            onChange={(e) => updateInsight({ tension: e.target.value })}
            placeholder="La fricción o conflicto interno que siente tu consumidor ideal..."
            className="min-h-[80px]"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="observation">Observación</Label>
          <Textarea
            id="observation"
            value={insight.observation || ""}
            onChange={(e) => updateInsight({ observation: e.target.value })}
            placeholder="Lo que observas en su comportamiento o contexto..."
            className="min-h-[80px]"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="implication">Implicación</Label>
          <Textarea
            id="implication"
            value={insight.implication || ""}
            onChange={(e) => updateInsight({ implication: e.target.value })}
            placeholder="Lo que eso significa para tu marca y cómo respondes..."
            className="min-h-[80px]"
          />
        </div>
      </div>

      {/* Benefits */}
      <div className="space-y-6 border-t pt-6">
        <h4 className="text-base font-semibold">Beneficios</h4>

        {/* Functional Benefits */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Beneficios Funcionales</Label>
            <Button type="button" variant="outline" size="sm" onClick={addFunctionalBenefit}>
              <Plus className="w-4 h-4 mr-2" />
              Agregar
            </Button>
          </div>
          {benefits.functional_benefits.map((b, i) => (
            <div key={i} className="flex gap-2 items-center">
              <Input
                value={b}
                onChange={(e) => updateFunctionalBenefit(i, e.target.value)}
                placeholder="Ej: Ahorra 10 horas semanales"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive h-8 w-8 flex-shrink-0"
                onClick={() => removeFunctionalBenefit(i)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}
          {benefits.functional_benefits.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-2 italic">
              Sin beneficios funcionales.
            </p>
          )}
        </div>

        {/* Emotional Benefits */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium">Beneficios Emocionales</Label>
            <Button type="button" variant="outline" size="sm" onClick={addEmotionalBenefit}>
              <Plus className="w-4 h-4 mr-2" />
              Agregar
            </Button>
          </div>
          {benefits.emotional_benefits.map((b, i) => (
            <div key={i} className="flex gap-2 items-center">
              <Input
                value={b}
                onChange={(e) => updateEmotionalBenefit(i, e.target.value)}
                placeholder="Ej: Sentir confianza al vender"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive h-8 w-8 flex-shrink-0"
                onClick={() => removeEmotionalBenefit(i)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}
          {benefits.emotional_benefits.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-2 italic">
              Sin beneficios emocionales.
            </p>
          )}
        </div>
      </div>

      {/* Submit */}
      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar Posicionamiento
        </Button>
      </div>
    </form>
  );
}
