"use client";

import { Copy, Pencil, Trash2 } from "lucide-react";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";

import { getVariantStructureMeta } from "../../lib/variant-structure-catalog";
import { EditionCard } from "../editions/EditionCard";
import { EditionStatusBadge } from "../editions/EditionStatusBadge";

import type { LaunchEdition } from "../../types";

interface VariantCardProps {
  variant: LaunchEdition;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

/**
 * Polymorphic variant card. Reads ``variant.variant_structure`` and
 * dispatches to the template appropriate for that shape:
 *
 * - ``temporal_*`` and ``recurring_intake`` → ``EditionCard`` (the existing
 *   temporal template showing dates + capacity).
 * - ``tier``     → tier card (price anchor + features differential).
 * - ``sku_variant`` → SKU card (attributes chips + inventory).
 * - ``regional`` → regional card (flag + currency + locale).
 * - ``modality`` → modality card (mode icon + logistics).
 * - ``language`` → language card (locale + translated copy).
 *
 * Plus a defensive fallback for unknown values (protects against backend
 * catalog drift). Every non-temporal template uses the same action row
 * (edit / duplicate / delete) for interaction parity with temporal
 * variants, so the collection landing's keyboard / hover / focus behavior
 * is identical regardless of structure.
 */
export function VariantCard(props: VariantCardProps) {
  const meta = getVariantStructureMeta(props.variant.variant_structure);

  // Temporal structures reuse the battle-tested EditionCard.
  const isTemporal =
    props.variant.variant_structure === "temporal_cohort" ||
    props.variant.variant_structure === "temporal_single_date" ||
    props.variant.variant_structure === "recurring_intake";

  if (isTemporal) {
    return <EditionCard edition={props.variant} {...pickActions(props)} />;
  }

  // Non-temporal dispatch by cardTemplate.
  switch (meta?.cardTemplate) {
    case "tier":
      return <TierVariantCard {...props} />;
    case "sku":
      return <SkuVariantCard {...props} />;
    case "regional":
      return <RegionalVariantCard {...props} />;
    case "modality":
      return <ModalityVariantCard {...props} />;
    case "language":
      return <LanguageVariantCard {...props} />;
    default:
      return <FallbackVariantCard {...props} />;
  }
}

function pickActions({
  onEdit,
  onDuplicate,
  onDelete,
}: VariantCardProps): Omit<VariantCardProps, "variant"> {
  return { onEdit, onDuplicate, onDelete };
}

// ─── Card action row (shared) ────────────────────────────────────────────────
function ActionRow({ onEdit, onDuplicate, onDelete }: Omit<VariantCardProps, "variant">) {
  return (
    <div className="mt-3 flex gap-1.5">
      <Button size="sm" variant="ghost" className="h-8 px-2.5 text-xs" onClick={onEdit}>
        <Pencil className="mr-1.5 h-3.5 w-3.5" />
        Editar
      </Button>
      <Button size="sm" variant="ghost" className="h-8 px-2.5 text-xs" onClick={onDuplicate}>
        <Copy className="mr-1.5 h-3.5 w-3.5" />
        Duplicar
      </Button>
      <Button
        size="sm"
        variant="ghost"
        className="ml-auto h-8 px-2.5 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
        onClick={onDelete}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}

// ─── TIER (planes Gold / Platinum / Enterprise) ─────────────────────────────
function TierVariantCard({ variant, ...actions }: VariantCardProps) {
  const price = useMemo(() => extractTierPrice(variant), [variant]);
  const features = useMemo(() => extractTierFeatures(variant), [variant]);

  return (
    <Card className={cn("border-l-4 border-l-purple-500", "transition-all hover:shadow-sm")}>
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground">{variant.edition_name}</h3>
          <EditionStatusBadge status={variant.status} />
        </div>
        {price && (
          <div className="mb-3">
            <span className="text-2xl font-bold tracking-tight">{price}</span>
            <span className="ml-1 text-xs text-muted-foreground">por ciclo</span>
          </div>
        )}
        {features.length > 0 && (
          <ul className="space-y-1 text-xs text-muted-foreground">
            {features.slice(0, 4).map((f) => (
              <li key={f} className="flex items-start gap-1.5">
                <span className="mt-0.5 h-1 w-1 shrink-0 rounded-full bg-purple-500" />
                <span>{f}</span>
              </li>
            ))}
            {features.length > 4 && (
              <li className="text-xs italic">+ {features.length - 4} beneficios más</li>
            )}
          </ul>
        )}
        <ActionRow {...actions} />
      </CardContent>
    </Card>
  );
}

// ─── SKU_VARIANT (talla / color / material) ─────────────────────────────────
function SkuVariantCard({ variant, ...actions }: VariantCardProps) {
  const sku = String(variant.structure_data?.sku_code ?? "—");
  const attributes = (variant.structure_data?.attributes ?? {}) as Record<string, string>;
  const attrPairs = Object.entries(attributes).slice(0, 4);

  return (
    <Card className="border-l-4 border-l-orange-500 transition-all hover:shadow-sm">
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground">{variant.edition_name}</h3>
          <EditionStatusBadge status={variant.status} />
        </div>
        <p className="mb-3 font-mono text-xs text-muted-foreground">SKU: {sku}</p>
        {attrPairs.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {attrPairs.map(([k, v]) => (
              <span
                key={k}
                className="rounded bg-muted px-2 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground"
              >
                {k}: {v}
              </span>
            ))}
          </div>
        )}
        {variant.capacity !== null && variant.capacity !== undefined && (
          <p className="mt-2 text-xs text-muted-foreground">
            Stock: <span className="font-semibold text-foreground">{variant.capacity}</span>
          </p>
        )}
        <ActionRow {...actions} />
      </CardContent>
    </Card>
  );
}

// ─── REGIONAL (por país) ────────────────────────────────────────────────────
function RegionalVariantCard({ variant, ...actions }: VariantCardProps) {
  const countries = (variant.structure_data?.country_codes ?? []) as string[];
  const currency = (variant.structure_data?.currency ?? "") as string;

  return (
    <Card className="border-l-4 border-l-sky-500 transition-all hover:shadow-sm">
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground">{variant.edition_name}</h3>
          <EditionStatusBadge status={variant.status} />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {countries.length > 0 ? (
            countries.map((code) => (
              <span
                key={code}
                className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-foreground"
              >
                {code.toUpperCase()}
              </span>
            ))
          ) : (
            <span className="text-xs italic text-muted-foreground">Sin países asignados</span>
          )}
          {currency && (
            <span className="ml-auto text-xs text-muted-foreground">
              Moneda: <span className="font-semibold text-foreground">{currency}</span>
            </span>
          )}
        </div>
        <ActionRow {...actions} />
      </CardContent>
    </Card>
  );
}

// ─── MODALITY (presencial / online / híbrido) ───────────────────────────────
function ModalityVariantCard({ variant, ...actions }: VariantCardProps) {
  const mode = String(variant.structure_data?.mode ?? "—");

  return (
    <Card className="border-l-4 border-l-teal-500 transition-all hover:shadow-sm">
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground">{variant.edition_name}</h3>
          <EditionStatusBadge status={variant.status} />
        </div>
        <span className="inline-flex rounded-md bg-teal-50 px-2 py-1 text-xs font-medium uppercase tracking-wide text-teal-700 dark:bg-teal-950 dark:text-teal-300">
          {mode}
        </span>
        {variant.location_override && (
          <p className="mt-2 text-xs text-muted-foreground">Logística específica configurada</p>
        )}
        <ActionRow {...actions} />
      </CardContent>
    </Card>
  );
}

// ─── LANGUAGE (idiomas) ─────────────────────────────────────────────────────
function LanguageVariantCard({ variant, ...actions }: VariantCardProps) {
  const locale = String(variant.structure_data?.locale ?? "—");

  return (
    <Card className="border-l-4 border-l-rose-500 transition-all hover:shadow-sm">
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-base font-semibold text-foreground">{variant.edition_name}</h3>
          <EditionStatusBadge status={variant.status} />
        </div>
        <span className="inline-flex rounded-md bg-rose-50 px-2 py-1 font-mono text-xs font-medium text-rose-700 dark:bg-rose-950 dark:text-rose-300">
          {locale.toUpperCase()}
        </span>
        <ActionRow {...actions} />
      </CardContent>
    </Card>
  );
}

// ─── Defensive fallback ─────────────────────────────────────────────────────
function FallbackVariantCard({ variant, ...actions }: VariantCardProps) {
  return (
    <Card className="border-l-4 border-l-muted-foreground transition-all hover:shadow-sm">
      <CardContent className="p-4">
        <h3 className="mb-1 text-base font-semibold text-foreground">{variant.edition_name}</h3>
        <p className="text-xs text-muted-foreground">
          Estructura <code className="rounded bg-muted px-1">{variant.variant_structure}</code> sin
          plantilla de card registrada.
        </p>
        <ActionRow {...actions} />
      </CardContent>
    </Card>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function extractTierPrice(variant: LaunchEdition): string | null {
  const priceAmount = variant.structure_data?.price_amount as number | undefined;
  const priceCurrency = variant.structure_data?.price_currency as string | undefined;
  if (priceAmount !== undefined && priceCurrency) {
    return formatMoney(priceAmount, priceCurrency);
  }
  const override = variant.pricing_override?.[0];
  if (override) return formatMoney(override.total_amount, override.currency ?? "USD");
  return null;
}

function extractTierFeatures(variant: LaunchEdition): readonly string[] {
  const features = variant.structure_data?.features;
  if (Array.isArray(features)) return features as string[];
  return [];
}
