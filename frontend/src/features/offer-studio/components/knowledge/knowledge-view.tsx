"use client";

import { ChangeEvent, useMemo, useRef, useState } from "react";
import {
  BookOpen,
  Download,
  ExternalLink,
  FileText,
  Info,
  Link as LinkIcon,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  Upload,
  Video,
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  useAddKnowledgeUrl,
  useDeleteKnowledge,
  useKnowledgeSources,
  useReindexKnowledge,
  useUploadKnowledge,
} from "../../hooks/use-knowledge";
import { useOfferShell } from "../container/offer-shell";
import type { KnowledgeListQuery, KnowledgeSourceResponse } from "../../types/knowledge";
import type { KnowledgeSourceType } from "../../types/enums";

type TypeFilter = "all" | "pdf" | "video" | "url";

const TYPE_FILTERS: { value: TypeFilter; label: string }[] = [
  { value: "all", label: "Todas" },
  { value: "pdf", label: "PDFs" },
  { value: "video", label: "Videos" },
  { value: "url", label: "URLs" },
];

const URL_TYPES: Set<KnowledgeSourceType> = new Set([
  "url_youtube",
  "url_article",
  "url_google_doc",
]);
const PDF_TYPES: Set<KnowledgeSourceType> = new Set(["pdf", "docx", "txt", "markdown"]);

const STATUS_LABEL: Record<string, string> = {
  indexed: "Indexado",
  processing: "Procesando",
  queued: "En cola",
  error: "Error",
};

const STATUS_CLASSES: Record<string, string> = {
  indexed: "bg-success/15 text-success border-success/30",
  processing: "bg-warning/15 text-warning border-warning/30",
  queued: "bg-muted/40 text-muted-foreground border-border",
  error: "bg-destructive/15 text-destructive border-destructive/30",
};

function matchesTypeFilter(source: KnowledgeSourceResponse, filter: TypeFilter): boolean {
  if (filter === "all") return true;
  if (filter === "url") return URL_TYPES.has(source.type);
  if (filter === "pdf") return PDF_TYPES.has(source.type);
  if (filter === "video") return source.type === "video";
  return true;
}

function SourceIcon({ type, className }: { type: KnowledgeSourceType; className?: string }) {
  if (URL_TYPES.has(type)) {
    return <LinkIcon className={className} aria-hidden />;
  }
  if (type === "video") {
    return <Video className={className} aria-hidden />;
  }
  return <FileText className={className} aria-hidden />;
}

function sourceIconColors(type: KnowledgeSourceType) {
  if (URL_TYPES.has(type)) return "bg-success/15 border-success/30 text-success";
  if (type === "video") return "bg-destructive/15 border-destructive/30 text-destructive";
  return "bg-info/15 border-info/30 text-info";
}

function formatRelativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 60) return `Hace ${Math.max(1, minutes)}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Hace ${days}d`;
  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `Hace ${weeks} sem`;
  const months = Math.floor(days / 30);
  return `Hace ${months} mes${months === 1 ? "" : "es"}`;
}

function formatBytes(bytes: number | null): string | null {
  if (bytes === null || bytes === 0) return null;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(0)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}

export function KnowledgeView({ offerId }: { offerId: string }) {
  const { offer } = useOfferShell();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [urlDialogOpen, setUrlDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<KnowledgeSourceResponse | null>(null);

  const query = useMemo<KnowledgeListQuery>(() => (search ? { search } : {}), [search]);

  const { data, isLoading, isError, error, refetch } = useKnowledgeSources(offerId, query);
  const upload = useUploadKnowledge(offerId);
  const addUrl = useAddKnowledgeUrl(offerId);
  const remove = useDeleteKnowledge(offerId);
  const reindex = useReindexKnowledge(offerId);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) upload.mutate(file);
    event.target.value = "";
  };

  const filteredItems = useMemo(
    () => (data?.items ?? []).filter((source) => matchesTypeFilter(source, typeFilter)),
    [data, typeFilter],
  );

  return (
    <div className="space-y-5 p-6" role="region" aria-label="Base de conocimiento">
      {/* Intro callout */}
      <Alert className="border-info/30 bg-info/5 text-foreground">
        <Info className="h-4 w-4 text-info" aria-hidden />
        <AlertTitle className="text-sm font-semibold">Para qué sirve esta base</AlertTitle>
        <AlertDescription className="text-xs text-muted-foreground">
          El Sales Agent lee estas fuentes para responder preguntas específicas sobre{" "}
          <strong className="text-foreground">{offer.name}</strong>. Cuando un cliente pregunte{" "}
          <em className="text-foreground">&ldquo;¿cuántos módulos son?&rdquo;</em>, el agente busca
          acá primero antes de responder. Sin fuentes, solo puede usar lo que está en el editor.
        </AlertDescription>
      </Alert>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-md flex-1">
          <Search
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden
          />
          <Input
            type="search"
            placeholder="Buscar fuente..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="pl-9"
            aria-label="Buscar fuente por nombre"
          />
        </div>

        <ChipGroup
          label="Tipo"
          value={typeFilter}
          options={TYPE_FILTERS}
          onChange={setTypeFilter}
        />

        <div className="h-6 w-px bg-border" aria-hidden />

        <Button
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => setUrlDialogOpen(true)}
        >
          <LinkIcon className="h-3.5 w-3.5" aria-hidden />
          Pegar URL
        </Button>
        <Button
          size="sm"
          className="gap-1.5"
          onClick={() => fileInputRef.current?.click()}
          disabled={upload.isPending}
        >
          {upload.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
          ) : (
            <Upload className="h-3.5 w-3.5" aria-hidden />
          )}
          Subir archivo
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFile}
          aria-hidden
        />
      </div>

      {/* List states */}
      {isLoading && <KnowledgeListSkeleton />}

      {isError && !isLoading && (
        <Alert variant="destructive">
          <AlertTitle>Error al cargar las fuentes</AlertTitle>
          <AlertDescription className="flex items-center justify-between gap-2">
            <span>{error?.message ?? "Intentalo nuevamente."}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => refetch()}>
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {!isLoading && !isError && data && filteredItems.length === 0 && (
        <KnowledgeEmptyState
          hasAny={data.items.length > 0}
          onUpload={() => fileInputRef.current?.click()}
          onAddUrl={() => setUrlDialogOpen(true)}
        />
      )}

      {!isLoading && !isError && filteredItems.length > 0 && (
        <ul role="list" aria-label="Lista de fuentes" className="space-y-2">
          {filteredItems.map((source) => (
            <KnowledgeSourceRow
              key={source.id}
              source={source}
              onReindex={() => reindex.mutate(source.id)}
              onDelete={() => setDeleteTarget(source)}
            />
          ))}
        </ul>
      )}

      {/* URL ingest dialog */}
      <KnowledgeUrlDialog
        open={urlDialogOpen}
        onOpenChange={setUrlDialogOpen}
        isPending={addUrl.isPending}
        onSubmit={(payload) => {
          addUrl.mutate(payload, {
            onSuccess: () => setUrlDialogOpen(false),
          });
        }}
      />

      {/* Delete confirm */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar fuente</AlertDialogTitle>
            <AlertDialogDescription>
              ¿Eliminar <strong>{deleteTarget?.name}</strong>? Se quitará del índice del Sales Agent
              y ya no la podrá citar en respuestas.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteTarget) {
                  remove.mutate(deleteTarget.id);
                  setDeleteTarget(null);
                }
              }}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ----------------------------------------------------------- Row

interface KnowledgeSourceRowProps {
  source: KnowledgeSourceResponse;
  onReindex: () => void;
  onDelete: () => void;
}

function KnowledgeSourceRow({ source, onReindex, onDelete }: KnowledgeSourceRowProps) {
  const iconClass = sourceIconColors(source.type);
  const statusLabel = STATUS_LABEL[source.status] ?? source.status;
  const statusClass = STATUS_CLASSES[source.status] ?? STATUS_CLASSES.queued;
  const isProcessing = source.status === "processing" || source.status === "queued";
  const size = formatBytes(source.size_bytes);

  const openSource = () => {
    const url = source.source_url ?? source.file_url;
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  };

  const downloadFile = () => {
    if (!source.file_url) return;
    const link = document.createElement("a");
    link.href = source.file_url;
    link.download = source.name;
    link.click();
  };

  const metadataParts: string[] = [];
  if (source.type) metadataParts.push(source.type.toUpperCase());
  if (size) metadataParts.push(size);
  metadataParts.push(formatRelativeDate(source.created_at));
  if (source.indexed_chunk_count > 0) {
    metadataParts.push(
      `${source.indexed_chunk_count} chunk${source.indexed_chunk_count === 1 ? "" : "s"}`,
    );
  }

  return (
    <li className="group flex items-center gap-3 rounded-lg border border-border p-3 hover:bg-card/40">
      <div
        className={cn(
          "flex h-10 w-10 flex-none items-center justify-center rounded-md border",
          iconClass,
        )}
      >
        {isProcessing ? (
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
        ) : (
          <SourceIcon type={source.type} className="h-5 w-5" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="truncate text-sm font-medium">{source.name}</p>
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide",
              statusClass,
            )}
          >
            {statusLabel}
          </span>
        </div>
        <p className="truncate text-[11px] text-muted-foreground">{metadataParts.join(" · ")}</p>
      </div>
      <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        {source.source_url || source.file_url ? (
          <Button variant="ghost" size="icon" aria-label="Abrir fuente" onClick={openSource}>
            <ExternalLink className="h-4 w-4 text-muted-foreground" aria-hidden />
          </Button>
        ) : null}
        {source.file_url ? (
          <Button variant="ghost" size="icon" aria-label="Descargar archivo" onClick={downloadFile}>
            <Download className="h-4 w-4 text-muted-foreground" aria-hidden />
          </Button>
        ) : null}
        <Button variant="ghost" size="icon" aria-label="Reindexar" onClick={onReindex}>
          <RefreshCw className="h-4 w-4 text-muted-foreground" aria-hidden />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Eliminar" onClick={onDelete}>
          <Trash2 className="h-4 w-4 text-destructive" aria-hidden />
        </Button>
      </div>
    </li>
  );
}

// ----------------------------------------------------------- Skeleton

function KnowledgeListSkeleton() {
  return (
    <div className="space-y-2" aria-label="Cargando fuentes">
      {Array.from({ length: 4 }).map((_, idx) => (
        <div key={idx} className="flex items-center gap-3 rounded-lg border border-border p-3">
          <Skeleton className="h-10 w-10 rounded-md" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-2/3" />
            <Skeleton className="h-2 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ----------------------------------------------------------- Empty

function KnowledgeEmptyState({
  hasAny,
  onUpload,
  onAddUrl,
}: {
  hasAny: boolean;
  onUpload: () => void;
  onAddUrl: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-muted/30">
        <BookOpen className="h-8 w-8 text-muted-foreground" aria-hidden />
      </div>
      <div className="space-y-1">
        <h3 className="font-semibold">
          {hasAny
            ? "No hay fuentes que coincidan con el filtro"
            : "Todavía no hay fuentes de conocimiento"}
        </h3>
        <p className="max-w-sm text-xs text-muted-foreground">
          Subí PDFs, webinars o pegá URLs para que el Sales Agent pueda responder preguntas
          específicas sobre esta oferta.
        </p>
      </div>
      {!hasAny && (
        <div className="flex flex-wrap justify-center gap-2">
          <Button variant="outline" size="sm" onClick={onAddUrl}>
            <LinkIcon className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Pegar URL
          </Button>
          <Button size="sm" onClick={onUpload}>
            <Upload className="mr-1.5 h-3.5 w-3.5" aria-hidden />
            Subir archivo
          </Button>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------- URL dialog

interface KnowledgeUrlDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  isPending: boolean;
  onSubmit: (payload: { url: string; name?: string }) => void;
}

function KnowledgeUrlDialog({ open, onOpenChange, isPending, onSubmit }: KnowledgeUrlDialogProps) {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");

  const handleSubmit = () => {
    if (!url.trim()) return;
    onSubmit({ url: url.trim(), name: name.trim() || undefined });
    setUrl("");
    setName("");
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!isPending) onOpenChange(next);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Agregar fuente desde URL</DialogTitle>
          <DialogDescription>
            Soportamos YouTube (transcripción automática), blog posts y Google Docs públicos.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div className="space-y-1.5">
            <Label htmlFor="knowledge-url">URL</Label>
            <Input
              id="knowledge-url"
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              disabled={isPending}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="knowledge-name">
              Nombre <span className="text-muted-foreground">(opcional)</span>
            </Label>
            <Input
              id="knowledge-name"
              type="text"
              placeholder="Webinar diseña tu 2026"
              value={name}
              onChange={(event) => setName(event.target.value)}
              disabled={isPending}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={isPending || !url.trim()}>
            {isPending && <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" aria-hidden />}
            Agregar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ----------------------------------------------------------- Chips

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
