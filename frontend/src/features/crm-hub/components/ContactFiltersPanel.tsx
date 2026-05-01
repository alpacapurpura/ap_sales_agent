"use client";

import { Check, ChevronDown } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

import { lifecycleStageSchema } from "../types";

import type { ContactFilterParams, LifecycleStage } from "../types";

interface ContactFiltersPanelProps {
  filters: ContactFilterParams;
  onChange: (filters: ContactFilterParams) => void;
  className?: string;
}

const LIFECYCLE_STAGES = lifecycleStageSchema.options;

const STAGE_LABELS: Record<LifecycleStage, string> = {
  subscriber: "Suscriptor",
  lead: "Lead",
  mql: "MQL",
  sql: "SQL",
  opportunity: "Oportunidad",
  customer: "Cliente",
  evangelist: "Evangelista",
  churned: "Churn",
};

const LATAM_COUNTRIES: { code: string; name: string }[] = [
  { code: "ar", name: "Argentina" },
  { code: "mx", name: "México" },
  { code: "co", name: "Colombia" },
  { code: "pe", name: "Perú" },
  { code: "cl", name: "Chile" },
  { code: "ec", name: "Ecuador" },
  { code: "bo", name: "Bolivia" },
  { code: "uy", name: "Uruguay" },
  { code: "py", name: "Paraguay" },
  { code: "ve", name: "Venezuela" },
];

function FilterLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
      {children}
    </p>
  );
}

/**
 * Panel lateral de filtros para la tabla de contactos.
 * Subconjunto lite S4 (8 tipos de filtro).
 * El resto de filtros PI-3 están en el schema TS pero sin UI hoy.
 */
export function ContactFiltersPanel({ filters, onChange, className }: ContactFiltersPanelProps) {
  const [stageOpen, setStageOpen] = React.useState(false);
  const [countryOpen, setCountryOpen] = React.useState(false);

  const scoreMin = filters.score_min ?? 0;
  const scoreMax = filters.score_max ?? 100;

  function toggleLifecycleStage(stage: LifecycleStage) {
    const current = filters.lifecycle_stage_in ?? [];
    const next = current.includes(stage) ? current.filter((s) => s !== stage) : [...current, stage];
    onChange({ ...filters, lifecycle_stage_in: next.length > 0 ? next : undefined });
  }

  function toggleCountry(code: string) {
    const current = filters.country_in ?? [];
    const next = current.includes(code) ? current.filter((c) => c !== code) : [...current, code];
    onChange({ ...filters, country_in: next.length > 0 ? next : undefined });
  }

  function setBoolean(
    key: "has_email" | "has_phone" | "has_telegram_id" | "is_inactive" | "has_campaign_engagement",
    value: boolean | undefined,
  ) {
    onChange({ ...filters, [key]: value });
  }

  function clearAll() {
    onChange({});
  }

  const hasFilters = Object.values(filters).some((v) => v !== undefined && v !== null);

  return (
    <ScrollArea className={cn("h-full", className)}>
      <div className="flex flex-col gap-4 p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-sm">Filtros</h2>
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearAll} className="h-auto py-0.5 text-xs">
              Limpiar
            </Button>
          )}
        </div>

        <Separator />

        {/* Etapa del ciclo de vida */}
        <div>
          <FilterLabel>Etapa</FilterLabel>
          <Popover open={stageOpen} onOpenChange={setStageOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between text-sm font-normal"
                aria-label="Seleccionar etapas"
              >
                <span className="truncate">
                  {filters.lifecycle_stage_in?.length
                    ? filters.lifecycle_stage_in.map((s) => STAGE_LABELS[s]).join(", ")
                    : "Todas las etapas"}
                </span>
                <ChevronDown className="ml-1 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-0" align="start">
              <Command>
                <CommandInput placeholder="Buscar etapa…" />
                <CommandList>
                  <CommandEmpty>Sin resultados.</CommandEmpty>
                  <CommandGroup>
                    {LIFECYCLE_STAGES.map((stage) => {
                      const selected = filters.lifecycle_stage_in?.includes(stage) ?? false;
                      return (
                        <CommandItem
                          key={stage}
                          value={stage}
                          onSelect={() => toggleLifecycleStage(stage)}
                        >
                          <Check
                            className={cn("mr-2 h-4 w-4", selected ? "opacity-100" : "opacity-0")}
                          />
                          {STAGE_LABELS[stage]}
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>

        {/* Score */}
        <div>
          <FilterLabel>Score</FilterLabel>
          <div className="px-1">
            <Slider
              min={0}
              max={100}
              step={1}
              value={[scoreMin, scoreMax]}
              onValueChange={([min, max]) => {
                onChange({
                  ...filters,
                  score_min: min === 0 ? undefined : min,
                  score_max: max === 100 ? undefined : max,
                });
              }}
              aria-label="Rango de score"
            />
            <div className="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>{scoreMin}</span>
              <span>{scoreMax}</span>
            </div>
          </div>
        </div>

        {/* Canales */}
        <div>
          <FilterLabel>Canales</FilterLabel>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Checkbox
                id="has-telegram"
                checked={filters.has_telegram_id ?? false}
                onCheckedChange={(v) =>
                  setBoolean("has_telegram_id", v === true ? true : undefined)
                }
              />
              <Label htmlFor="has-telegram" className="text-sm font-normal cursor-pointer">
                Telegram
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="has-email"
                checked={filters.has_email ?? false}
                onCheckedChange={(v) => setBoolean("has_email", v === true ? true : undefined)}
              />
              <Label htmlFor="has-email" className="text-sm font-normal cursor-pointer">
                Email
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="has-phone"
                checked={filters.has_phone ?? false}
                onCheckedChange={(v) => setBoolean("has_phone", v === true ? true : undefined)}
              />
              <Label htmlFor="has-phone" className="text-sm font-normal cursor-pointer">
                Teléfono
              </Label>
            </div>
          </div>
        </div>

        {/* Otros */}
        <div>
          <FilterLabel>Otros</FilterLabel>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Checkbox
                id="is-inactive"
                checked={filters.is_inactive ?? false}
                onCheckedChange={(v) => setBoolean("is_inactive", v === true ? true : undefined)}
              />
              <Label htmlFor="is-inactive" className="text-sm font-normal cursor-pointer">
                Inactivos
              </Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="has-campaign"
                checked={filters.has_campaign_engagement ?? false}
                onCheckedChange={(v) =>
                  setBoolean("has_campaign_engagement", v === true ? true : undefined)
                }
              />
              <Label htmlFor="has-campaign" className="text-sm font-normal cursor-pointer">
                Recibió campaña últimos 90d
              </Label>
            </div>
          </div>
        </div>

        {/* País */}
        <div>
          <FilterLabel>País</FilterLabel>
          <Popover open={countryOpen} onOpenChange={setCountryOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-between text-sm font-normal"
                aria-label="Seleccionar países"
              >
                <span className="truncate">
                  {filters.country_in?.length
                    ? filters.country_in.map((c) => c.toUpperCase()).join(", ")
                    : "Todos los países"}
                </span>
                <ChevronDown className="ml-1 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-56 p-0" align="start">
              <Command>
                <CommandInput placeholder="Buscar país…" />
                <CommandList>
                  <CommandEmpty>Sin resultados.</CommandEmpty>
                  <CommandGroup>
                    {LATAM_COUNTRIES.map(({ code, name }) => {
                      const selected = filters.country_in?.includes(code) ?? false;
                      return (
                        <CommandItem key={code} value={code} onSelect={() => toggleCountry(code)}>
                          <Check
                            className={cn("mr-2 h-4 w-4", selected ? "opacity-100" : "opacity-0")}
                          />
                          {code.toUpperCase()} — {name}
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        </div>
      </div>
    </ScrollArea>
  );
}
