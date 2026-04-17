"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
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

import { EditionStatus } from "../../types";

import { EditionPricingOverride } from "./EditionPricingOverride";

import type {
  LaunchEdition,
  LaunchEditionCreate,
  LaunchEditionUpdate,
  PricingStructure,
} from "../../types";

interface EditionFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  edition?: LaunchEdition;
  offerPricing: PricingStructure[] | undefined;
  currency: string;
  onSave: (data: LaunchEditionCreate | LaunchEditionUpdate) => Promise<unknown>;
}

function toLocalInputValue(isoString: string | null | undefined): string {
  if (!isoString) return "";
  const d = new Date(isoString);
  const offset = d.getTimezoneOffset();
  const local = new Date(d.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

function fromLocalInputValue(value: string): string | undefined {
  if (!value) return undefined;
  return new Date(value).toISOString();
}

export function EditionFormDialog({
  open,
  onOpenChange,
  edition,
  offerPricing,
  currency,
  onSave,
}: EditionFormDialogProps) {
  const isEdit = !!edition;

  const [name, setName] = useState(edition?.edition_name ?? "");
  const [startDate, setStartDate] = useState(toLocalInputValue(edition?.start_date));
  const [endDate, setEndDate] = useState(toLocalInputValue(edition?.end_date));
  const [regStart, setRegStart] = useState(toLocalInputValue(edition?.registration_start));
  const [regEnd, setRegEnd] = useState(toLocalInputValue(edition?.registration_end));
  const [tz] = useState(edition?.timezone ?? "America/Lima");
  const [capacity, setCapacity] = useState<string>(edition?.capacity?.toString() ?? "");
  const [status, setStatus] = useState<EditionStatus>(edition?.status ?? EditionStatus.DRAFT);
  const [pricingOverride, setPricingOverride] = useState<PricingStructure[] | null>(
    edition?.pricing_override ?? null,
  );
  const [notes, setNotes] = useState(edition?.notes ?? "");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      // start_date is optional — placeholder editions may be saved with no
      // date. Domain validators block publish transitions when missing.
      const data: LaunchEditionCreate & LaunchEditionUpdate = {
        edition_name: name || undefined,
        start_date: fromLocalInputValue(startDate),
        end_date: fromLocalInputValue(endDate),
        registration_start: fromLocalInputValue(regStart),
        registration_end: fromLocalInputValue(regEnd),
        timezone: tz,
        capacity: capacity ? parseInt(capacity, 10) : undefined,
        pricing_override: pricingOverride ?? undefined,
        notes: notes || undefined,
      };
      if (isEdit) {
        (data as LaunchEditionUpdate).status = status;
      }
      await onSave(data);
      onOpenChange(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar Edición" : "Nueva Edición"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Name */}
          <div className="space-y-1">
            <Label className="text-xs">Nombre de la Edición</Label>
            <Input
              placeholder="Se auto-genera si lo dejas vacío"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Fecha de Inicio</Label>
              <Input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
              <p className="text-[.65rem] text-muted-foreground">
                Opcional — debes fijarla antes de publicar la edición.
              </p>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha de Fin</Label>
              <Input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Inscripciones Desde</Label>
              <Input
                type="datetime-local"
                value={regStart}
                onChange={(e) => setRegStart(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Inscripciones Hasta</Label>
              <Input
                type="datetime-local"
                value={regEnd}
                onChange={(e) => setRegEnd(e.target.value)}
              />
            </div>
          </div>

          {/* Capacity + Status */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Capacidad Máxima</Label>
              <Input
                type="number"
                placeholder="Sin límite"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
              />
            </div>
            {isEdit && (
              <div className="space-y-1">
                <Label className="text-xs">Estado</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as EditionStatus)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={EditionStatus.DRAFT}>Borrador</SelectItem>
                    <SelectItem value={EditionStatus.UPCOMING}>Próximo</SelectItem>
                    <SelectItem value={EditionStatus.ACTIVE}>En Curso</SelectItem>
                    <SelectItem value={EditionStatus.COMPLETED}>Completado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Pricing Override */}
          <EditionPricingOverride
            offerPricing={offerPricing}
            currency={currency}
            value={pricingOverride}
            onChange={setPricingOverride}
          />

          {/* Notes */}
          <div className="space-y-1">
            <Label className="text-xs">Notas Internas</Label>
            <Textarea
              placeholder="Notas visibles solo para ti..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEdit ? "Guardar Cambios" : "Crear Edición"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
