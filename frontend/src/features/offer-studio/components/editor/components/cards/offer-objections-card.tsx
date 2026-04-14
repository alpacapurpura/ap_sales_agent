"use client";

import { useFieldArray, Control } from "react-hook-form";
import { OfferFormValues } from "../../../../types/schema";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Trash2, Shield } from "lucide-react";
import TextareaAutosize from "react-textarea-autosize";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

const OBJECTION_TYPES = [
  { value: "price", label: "Precio" },
  { value: "time", label: "Tiempo" },
  { value: "trust", label: "Confianza" },
  { value: "partner", label: "Socio/Pareja" },
  { value: "fear", label: "Miedo" },
  { value: "medical", label: "Salud" },
  { value: "is_ai", label: "¿Eres IA?" },
  { value: "tech", label: "Técnico" },
  { value: "custom", label: "Otro" },
] as const;

const STRATEGY_OPTIONS = [
  "ROI Reframing",
  "Paradox",
  "Risk Reversal",
  "Social Proof",
  "Empathy Protocol",
  "Business Plan",
  "Transparency",
  "Urgency",
  "Manual Rescue",
] as const;

interface OfferObjectionsCardProps {
  control: Control<OfferFormValues>;
}

export function OfferObjectionsCard({ control }: OfferObjectionsCardProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: "objections",
  });

  const handleAdd = () => {
    append({
      id: crypto.randomUUID(),
      type: "custom",
      trigger_phrases: [],
      strategy: "",
      rebuttal: "",
    });
  };

  return (
    <Card className="border-dashed shadow-sm overflow-hidden">
      <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0 bg-amber-50/50 dark:bg-amber-900/10 border-b">
        <CardTitle className="text-base font-medium flex items-center gap-2">
          <Shield className="h-4 w-4 text-amber-600" />
          Objeciones Comunes
          {fields.length > 0 && (
            <Badge
              variant="secondary"
              className="text-[10px] h-5 px-1.5 bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
            >
              {fields.length}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="p-4 space-y-4">
        {fields.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center space-y-3">
            <div className="p-3 bg-amber-100 dark:bg-amber-900/30 rounded-full">
              <Shield className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            </div>
            <div className="space-y-1 max-w-sm">
              <h3 className="font-semibold text-sm">Sin Objeciones Definidas</h3>
              <p className="text-xs text-muted-foreground">
                Define las objeciones comunes de tus clientes para que tu agente de ventas sepa cómo
                manejarlas.
              </p>
            </div>
          </div>
        )}

        <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1 custom-scrollbar">
          {fields.map((field, index) => (
            <div
              key={field.id}
              className="group relative border rounded-lg p-4 space-y-3 bg-background hover:border-amber-300 dark:hover:border-amber-700 transition-colors"
            >
              {/* Header: Type + Strategy + Delete */}
              <div className="flex gap-2 items-center">
                <Select
                  defaultValue={field.type || "custom"}
                  onValueChange={(val) => {
                    control._formValues.objections[index].type = val;
                  }}
                >
                  <SelectTrigger className="w-[140px] h-8 text-xs">
                    <SelectValue placeholder="Tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {OBJECTION_TYPES.map((t) => (
                      <SelectItem key={t.value} value={t.value} className="text-xs">
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Input
                  {...control.register(`objections.${index}.strategy`)}
                  placeholder="Estrategia (ej: ROI Reframing)"
                  className="h-8 text-xs flex-1"
                  list="strategy-options"
                />
                <datalist id="strategy-options">
                  {STRATEGY_OPTIONS.map((s) => (
                    <option key={s} value={s} />
                  ))}
                </datalist>

                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => remove(index)}
                  className="h-8 w-8 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>

              {/* Trigger Phrases */}
              <div>
                <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                  Frases que lo disparan
                </label>
                <Input
                  {...control.register(`objections.${index}.trigger_phrases`, {
                    setValueAs: (v: unknown) =>
                      typeof v === "string"
                        ? v
                            .split(",")
                            .map((s: string) => s.trim())
                            .filter(Boolean)
                        : v,
                  })}
                  placeholder="es caro, no me alcanza, mucha plata (separar con comas)"
                  className="h-8 text-xs mt-1"
                  defaultValue={
                    Array.isArray(field.trigger_phrases)
                      ? field.trigger_phrases.join(", ")
                      : ""
                  }
                />
              </div>

              {/* Rebuttal Script */}
              <div>
                <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                  Respuesta del agente
                </label>
                <TextareaAutosize
                  {...control.register(`objections.${index}.rebuttal`)}
                  placeholder="Te entiendo, es una inversión importante. Pero piénsalo así..."
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-500 disabled:cursor-not-allowed disabled:opacity-50 resize-none transition-all hover:border-amber-500/50 mt-1"
                  minRows={2}
                />
              </div>
            </div>
          ))}
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="w-full text-xs h-8 border border-dashed border-amber-200 dark:border-amber-900/50 hover:bg-amber-50 dark:hover:bg-amber-950/30 text-amber-600 dark:text-amber-400"
          onClick={handleAdd}
        >
          <Plus className="h-3 w-3 mr-1" /> Agregar Objeción
        </Button>
      </CardContent>
    </Card>
  );
}
