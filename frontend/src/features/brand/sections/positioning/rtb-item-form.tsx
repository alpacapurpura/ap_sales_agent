"use client";

import { Trash2 } from "lucide-react";

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
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

import type { ReasonToBelieve } from "@/features/brand/types";

interface RtbItemFormProps {
  rtb: ReasonToBelieve;
  onChange: (rtb: ReasonToBelieve) => void;
  onRemove: () => void;
}

const RTB_TYPE_OPTIONS = [
  { value: "dato", label: "Dato" },
  { value: "caso_exito", label: "Caso de Éxito" },
  { value: "certificacion", label: "Certificación" },
  { value: "tecnologia", label: "Tecnología" },
  { value: "proceso", label: "Proceso" },
];

export function RtbItemForm({ rtb, onChange, onRemove }: RtbItemFormProps) {
  return (
    <div className="flex gap-3 items-start p-3 bg-muted/20 rounded-lg border">
      <div className="flex-1 space-y-3">
        <div className="grid grid-cols-[140px_1fr] gap-2">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Tipo</Label>
            <Select value={rtb.type || ""} onValueChange={(val) => onChange({ ...rtb, type: val })}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="Seleccionar..." />
              </SelectTrigger>
              <SelectContent>
                {RTB_TYPE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Declaración</Label>
            <WithCopilot
              fieldId={`rtb_${rtb.id}_statement`}
              fieldLabel="RTB Declaración"
              getValue={() => rtb.statement || ""}
            >
              <Input
                value={rtb.statement || ""}
                onChange={(e) => onChange({ ...rtb, statement: e.target.value })}
                placeholder="Ej: +500 clientes atendidos en 12 meses"
                className="h-9"
              />
            </WithCopilot>
          </div>
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">URL de Prueba (opcional)</Label>
          <Input
            value={rtb.proof_url || ""}
            onChange={(e) => onChange({ ...rtb, proof_url: e.target.value })}
            placeholder="https://..."
            className="h-9"
          />
        </div>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="text-muted-foreground hover:text-destructive h-8 w-8 mt-5"
        onClick={onRemove}
      >
        <Trash2 className="w-4 h-4" />
      </Button>
    </div>
  );
}
