"use client";

import { FileText, Upload, X, ArrowRight, ArrowLeft } from "lucide-react";
import { useCallback } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface StepDocumentsProps {
  files: File[];
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onNext: () => void;
  onBack: () => void;
}

const ACCEPTED_TYPES = ".pdf,.docx,.txt,.md,.pptx";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function StepDocuments({
  files,
  onAddFiles,
  onRemoveFile,
  onNext,
  onBack,
}: StepDocumentsProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const droppedFiles = Array.from(e.dataTransfer.files);
      onAddFiles(droppedFiles);
    },
    [onAddFiles],
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        onAddFiles(Array.from(e.target.files));
        e.target.value = "";
      }
    },
    [onAddFiles],
  );

  return (
    <div className="mx-auto max-w-lg animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
          <FileText className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Sube tus documentos</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          PDFs, presentaciones, documentos de marca — lo que tengas.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className={cn(
          "relative flex min-h-[160px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors",
          "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30",
        )}
      >
        <Upload className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Arrastra archivos aquí</p>
        <p className="mt-1 text-xs text-muted-foreground">o haz click para seleccionar</p>
        <input
          type="file"
          accept={ACCEPTED_TYPES}
          multiple
          onChange={handleFileInput}
          className="absolute inset-0 cursor-pointer opacity-0"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, idx) => (
            <div
              key={`${file.name}-${idx}`}
              className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-2.5"
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText className="h-4 w-4 flex-shrink-0 text-primary" />
                <div className="overflow-hidden">
                  <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRemoveFile(idx)}
                className="ml-2 flex-shrink-0 rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <p className="mt-3 text-xs text-muted-foreground">
        Formatos aceptados: PDF, DOCX, TXT, MD, PPTX
      </p>

      <div className="mt-8 flex justify-between">
        <Button variant="ghost" onClick={onBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Atrás
        </Button>
        <Button onClick={onNext} disabled={files.length === 0} className="gap-2">
          Continuar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
