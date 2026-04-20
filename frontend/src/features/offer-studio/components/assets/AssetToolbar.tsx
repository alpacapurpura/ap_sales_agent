"use client";

import { ArrowUpDown, Search, Sparkles, Upload } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import type { AssetSortKey } from "../../types/assets";
import type { OfferAssetSource, OfferAssetType } from "../../types/enums";
import type { ChangeEvent } from "react";

export interface AssetToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;

  type: OfferAssetType | "all";
  onTypeChange: (value: OfferAssetType | "all") => void;

  source: OfferAssetSource | "all";
  onSourceChange: (value: OfferAssetSource | "all") => void;

  sort: AssetSortKey;
  onSortChange: (value: AssetSortKey) => void;

  totalShown: number;
  totalAssets: number;

  onUpload: (file: File) => void;
  isUploading?: boolean;
  onGenerate: () => void;
}

const TYPE_LABELS: { value: OfferAssetType | "all"; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "video", label: "Videos" },
  { value: "flyer", label: "Flyers" },
  { value: "carousel", label: "Carruseles" },
  { value: "document", label: "Docs" },
];

const SOURCE_LABELS: { value: OfferAssetSource | "all"; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "ai", label: "IA" },
  { value: "external", label: "Externos" },
];

const SORT_LABELS: Record<AssetSortKey, string> = {
  created_desc: "Recientes primero",
  created_asc: "Más antiguos",
  name_asc: "Nombre A-Z",
  name_desc: "Nombre Z-A",
};

/**
 *
 */
export function AssetToolbar({
  search,
  onSearchChange,
  type,
  onTypeChange,
  source,
  onSourceChange,
  sort,
  onSortChange,
  totalShown,
  totalAssets,
  onUpload,
  isUploading,
  onGenerate,
}: AssetToolbarProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) onUpload(file);
    event.target.value = "";
  };

  return (
    <div className="space-y-3">
      {/* Row 1: search + sort + actions */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-md flex-1">
          <Search
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            type="search"
            placeholder="Buscar asset por nombre..."
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            className="pl-9"
            aria-label="Buscar asset por nombre"
          />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-1.5">
              <ArrowUpDown className="h-3.5 w-3.5" aria-hidden />
              {SORT_LABELS[sort]}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {(Object.entries(SORT_LABELS) as [AssetSortKey, string][]).map(([key, label]) => (
              <DropdownMenuItem key={key} onClick={() => onSortChange(key)}>
                {label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="h-6 w-px bg-border" aria-hidden />

        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          <Upload className="h-3.5 w-3.5" aria-hidden />
          Subir externo
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          aria-hidden
        />

        <Button size="sm" className="gap-1.5" onClick={onGenerate}>
          <Sparkles className="h-3.5 w-3.5" aria-hidden />
          Generar con IA
        </Button>
      </div>

      {/* Row 2: type + source filters + counter */}
      <div className="flex flex-wrap items-center gap-4">
        <ChipGroup label="Tipo" value={type} options={TYPE_LABELS} onChange={onTypeChange} />
        <div className="hidden h-5 w-px bg-border md:block" aria-hidden />
        <ChipGroup
          label="Origen"
          value={source}
          options={SOURCE_LABELS}
          onChange={onSourceChange}
        />
        <div className="ml-auto text-[11px] text-muted-foreground">
          Mostrando <strong className="text-foreground">{totalShown}</strong> de{" "}
          <strong className="text-foreground">{totalAssets}</strong>{" "}
          {totalAssets === 1 ? "asset" : "assets"}
        </div>
      </div>
    </div>
  );
}

interface ChipGroupProps<T extends string> {
  label: string;
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
}

function ChipGroup<T extends string>({ label, value, options, onChange }: ChipGroupProps<T>) {
  return (
    <div className="flex items-center gap-2" role="group" aria-label={label}>
      <span className="text-[10px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <div className="flex items-center rounded-md border border-border bg-card p-0.5 text-xs">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              type="button"
              key={opt.value}
              onClick={() => onChange(opt.value)}
              aria-pressed={active}
              className={cn(
                "rounded px-2.5 py-1 transition-colors",
                active
                  ? "bg-muted font-medium text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
