"use client";

import { useState, useEffect } from "react";
import {
  BrandNarrative,
  StoryBrandPlanStep,
} from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  User,
  AlertTriangle,
  Compass,
  ListOrdered,
  Megaphone,
  TrendingUp,
  MessageSquareQuote,
  Plus,
  Trash2,
  Save,
  Loader2,
} from "lucide-react";

interface NarrativeFormProps {
  narrative: BrandNarrative;
  onSave: (data: BrandNarrative) => Promise<void>;
  isSaving: boolean;
}

export function NarrativeForm({ narrative, onSave, isSaving }: NarrativeFormProps) {
  const [form, setForm] = useState<BrandNarrative>(narrative);

  useEffect(() => {
    setForm(narrative);
  }, [narrative]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(form);
  };

  // --- Hero ---
  const updateHero = (field: "identity" | "desire", value: string) => {
    setForm({ ...form, hero: { ...form.hero, [field]: value } });
  };

  // --- Problem ---
  const updateProblem = (
    field: "villain" | "external_problem" | "internal_problem" | "philosophical_problem",
    value: string
  ) => {
    setForm({ ...form, problem: { ...form.problem, [field]: value } });
  };

  // --- Guide ---
  const updateGuide = (
    field: "empathy_statement" | "authority_statement",
    value: string
  ) => {
    setForm({ ...form, guide: { ...form.guide, [field]: value } });
  };

  // --- Plan ---
  const addStep = () => {
    const nextNumber = form.plan.length + 1;
    const newStep: StoryBrandPlanStep = {
      id: crypto.randomUUID(),
      step_number: nextNumber,
      title: "",
      description: "",
    };
    setForm({ ...form, plan: [...form.plan, newStep] });
  };

  const updateStep = (id: string, field: "title" | "description", value: string) => {
    const updated = form.plan.map((s) =>
      s.id === id ? { ...s, [field]: value } : s
    );
    setForm({ ...form, plan: updated });
  };

  const removeStep = (id: string) => {
    const filtered = form.plan
      .filter((s) => s.id !== id)
      .map((s, idx) => ({ ...s, step_number: idx + 1 }));
    setForm({ ...form, plan: filtered });
  };

  // --- CTA ---
  const updateCta = (field: "direct_cta" | "transitional_cta", value: string) => {
    setForm({ ...form, cta: { ...form.cta, [field]: value } });
  };

  // --- Outcome ---
  const updateOutcome = (
    field: "success_transformation" | "failure_consequence",
    value: string
  ) => {
    setForm({ ...form, outcome: { ...form.outcome, [field]: value } });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-10">
      {/* ── 1. Hero ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <User className="w-5 h-5" />
          <h3 className="font-medium">1. El Heroe</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Tu cliente es el heroe de la historia. Define quien es y que desea.
        </p>
        <div className="space-y-2">
          <Label htmlFor="hero_identity">Identidad del Heroe</Label>
          <Textarea
            id="hero_identity"
            value={form.hero?.identity ?? ""}
            onChange={(e) => updateHero("identity", e.target.value)}
            placeholder="Ej: Emprendedoras que venden cursos online y quieren escalar..."
            className="h-20"
          />
          <p className="text-xs text-muted-foreground">
            Si tienes avatares definidos en El Publico (Cap 7), tu heroe es tu avatar principal.
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="hero_desire">Deseo Principal</Label>
          <Textarea
            id="hero_desire"
            value={form.hero?.desire ?? ""}
            onChange={(e) => updateHero("desire", e.target.value)}
            placeholder="Ej: Quiere automatizar sus ventas para tener mas tiempo libre..."
            className="h-20"
          />
        </div>
      </section>

      <Separator />

      {/* ── 2. Problem ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <AlertTriangle className="w-5 h-5" />
          <h3 className="font-medium">2. El Problema</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Identifica el villano y los tres niveles de problema que enfrenta tu heroe.
        </p>
        <div className="space-y-2">
          <Label htmlFor="villain">Villano</Label>
          <Input
            id="villain"
            value={form.problem?.villain ?? ""}
            onChange={(e) => updateProblem("villain", e.target.value)}
            placeholder="Ej: La complejidad del marketing digital"
          />
          <p className="text-xs text-muted-foreground">
            El antagonista que causa la frustracion de tu cliente. Si ya definiste enemigos en Diferenciacion (Cap 2), tu villano suele ser una combinacion de ambos.
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="external_problem">Problema Externo</Label>
          <Textarea
            id="external_problem"
            value={form.problem?.external_problem ?? ""}
            onChange={(e) => updateProblem("external_problem", e.target.value)}
            placeholder="Ej: No tienen tiempo ni equipo para gestionar campanas..."
            className="h-20"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="internal_problem">Problema Interno</Label>
          <Textarea
            id="internal_problem"
            value={form.problem?.internal_problem ?? ""}
            onChange={(e) => updateProblem("internal_problem", e.target.value)}
            placeholder="Ej: Se sienten abrumadas y con miedo de gastar dinero sin resultados..."
            className="h-20"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="philosophical_problem">Problema Filosofico</Label>
          <Textarea
            id="philosophical_problem"
            value={form.problem?.philosophical_problem ?? ""}
            onChange={(e) => updateProblem("philosophical_problem", e.target.value)}
            placeholder="Ej: No deberia ser tan dificil vender algo que transforma vidas..."
            className="h-20"
          />
        </div>
      </section>

      <Separator />

      {/* ── 3. Guide ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <Compass className="w-5 h-5" />
          <h3 className="font-medium">3. El Guia</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Tu marca es el guia. Demuestra empatia y autoridad.
        </p>
        <div className="space-y-2">
          <Label htmlFor="empathy_statement">Declaracion de Empatia</Label>
          <Textarea
            id="empathy_statement"
            value={form.guide?.empathy_statement ?? ""}
            onChange={(e) => updateGuide("empathy_statement", e.target.value)}
            placeholder="Ej: Sabemos lo frustrante que es invertir en marketing y no ver resultados..."
            className="h-20"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="authority_statement">Declaracion de Autoridad</Label>
          <Textarea
            id="authority_statement"
            value={form.guide?.authority_statement ?? ""}
            onChange={(e) => updateGuide("authority_statement", e.target.value)}
            placeholder="Ej: Hemos ayudado a mas de 500 emprendedoras a duplicar sus ventas..."
            className="h-20"
          />
          <p className="text-xs text-muted-foreground">
            Usa tus mejores datos del Vault de Autoridad (Cap 9) para construir esta declaracion.
          </p>
        </div>
      </section>

      <Separator />

      {/* ── 4. Plan ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <ListOrdered className="w-5 h-5" />
          <h3 className="font-medium">4. El Plan</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Define los pasos claros que tu cliente debe seguir. Maximo 4 pasos. Si tu marca tiene una metodologia (Cap 1), tus pasos suelen alinearse con sus pilares — pero redactalos desde la perspectiva del CLIENTE.
        </p>

        <div className="space-y-4">
          {form.plan.map((step) => (
            <div
              key={step.id}
              className="flex gap-4 items-start p-4 bg-muted/20 rounded-lg border relative"
            >
              <div className="flex items-center justify-center h-6 w-6 rounded-full bg-primary/10 text-primary text-xs font-bold mt-1 shrink-0">
                {step.step_number}
              </div>
              <div className="space-y-3 flex-1">
                <div>
                  <Label className="text-xs text-muted-foreground">Titulo del Paso</Label>
                  <Input
                    value={step.title ?? ""}
                    onChange={(e) => updateStep(step.id, "title", e.target.value)}
                    placeholder="Ej: Agenda una llamada"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Descripcion</Label>
                  <Textarea
                    value={step.description ?? ""}
                    onChange={(e) => updateStep(step.id, "description", e.target.value)}
                    placeholder="Breve descripcion de este paso..."
                    className="h-16 text-sm"
                  />
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-muted-foreground hover:text-destructive absolute top-2 right-2"
                onClick={() => removeStep(step.id)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}

          {form.plan.length === 0 && (
            <div className="text-center py-8 border-2 border-dashed rounded-lg">
              <p className="text-sm text-muted-foreground">
                No has definido los pasos del plan.
              </p>
            </div>
          )}
        </div>

        <Button type="button" variant="outline" size="sm" onClick={addStep}>
          <Plus className="w-4 h-4 mr-2" />
          Agregar Paso
        </Button>
      </section>

      <Separator />

      {/* ── 5. CTA ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <Megaphone className="w-5 h-5" />
          <h3 className="font-medium">5. Llamada a la Accion</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          El CTA directo es la accion principal. El transicional es para quienes aun no estan listos.
        </p>
        <div className="space-y-2">
          <Label htmlFor="direct_cta">CTA Directo</Label>
          <Input
            id="direct_cta"
            value={form.cta?.direct_cta ?? ""}
            onChange={(e) => updateCta("direct_cta", e.target.value)}
            placeholder="Ej: Agenda tu demo gratis"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="transitional_cta">CTA Transicional</Label>
          <Input
            id="transitional_cta"
            value={form.cta?.transitional_cta ?? ""}
            onChange={(e) => updateCta("transitional_cta", e.target.value)}
            placeholder="Ej: Descarga la guia gratuita"
          />
        </div>
      </section>

      <Separator />

      {/* ── 6. Outcome ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <TrendingUp className="w-5 h-5" />
          <h3 className="font-medium">6. Resultado</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Pinta la imagen del exito y del fracaso. El contraste motiva la accion.
        </p>
        <div className="space-y-2">
          <Label htmlFor="success_transformation">Transformacion de Exito</Label>
          <Textarea
            id="success_transformation"
            value={form.outcome?.success_transformation ?? ""}
            onChange={(e) => updateOutcome("success_transformation", e.target.value)}
            placeholder="Ej: Ventas en piloto automatico, mas tiempo para crear contenido..."
            className="h-20"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="failure_consequence">Consecuencia del Fracaso</Label>
          <Textarea
            id="failure_consequence"
            value={form.outcome?.failure_consequence ?? ""}
            onChange={(e) => updateOutcome("failure_consequence", e.target.value)}
            placeholder="Ej: Seguir perdiendo clientes y quemando presupuesto sin resultados..."
            className="h-20"
          />
        </div>
      </section>

      <Separator />

      {/* ── 7. One-liner ── */}
      <section className="space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b text-primary">
          <MessageSquareQuote className="w-5 h-5" />
          <h3 className="font-medium">7. One-Liner</h3>
        </div>
        <p className="text-xs text-muted-foreground">
          Tu pitch de venta en 1 oracion. Formato: Problema + Solucion + Resultado. El SDR lo usa para abrir conversaciones.
        </p>
        <div className="space-y-2">
          <Label htmlFor="one_liner">Tu One-Liner</Label>
          <Textarea
            id="one_liner"
            value={form.one_liner ?? ""}
            onChange={(e) => setForm({ ...form, one_liner: e.target.value })}
            placeholder="Ej: La mayoria de emprendedoras pierden clientes por no dar seguimiento. Nicolify automatiza tu cierre de ventas para que vendas mas sin contratar equipo."
            className="h-24"
          />
        </div>
      </section>

      {/* ── Save ── */}
      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={isSaving}>
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Guardar Narrativa
        </Button>
      </div>
    </form>
  );
}
