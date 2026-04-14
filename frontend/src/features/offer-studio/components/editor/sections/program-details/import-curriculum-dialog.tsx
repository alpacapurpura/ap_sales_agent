"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";

interface ImportCurriculumDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (modules: any[]) => void;
}

export function ImportCurriculumDialog({
  open,
  onOpenChange,
  onImport,
}: ImportCurriculumDialogProps) {
  const [importText, setImportText] = useState("");
  const [isImporting, setIsImporting] = useState(false);

  const handleSmartImport = () => {
    if (!importText.trim()) return;
    setIsImporting(true);

    try {
      // 1. Detect Modules (e.g., "Module 1:", "Week 1:", "Semana 1:")
      // Regex looks for lines starting with typical module headers
      const lines = importText.split("\n");
      const modules: any[] = [];
      let currentModule: any = null;

      lines.forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed) return;

        // Detection Logic
        const isModuleHeader =
          /^(module|módulo|week|semana|phase|fase)\s+\d+[:\.]?/i.test(trimmed) ||
          /^\d+\.\s+[A-Z]/.test(trimmed);

        if (isModuleHeader || !currentModule) {
          // New Module
          currentModule = {
            title: trimmed.replace(/[:\.]\s*$/, ""),
            description: "",
            topics: [],
          };
          modules.push(currentModule);
        } else {
          // It's a topic or description
          if (trimmed.startsWith("-") || trimmed.startsWith("•")) {
            currentModule.topics.push(trimmed.replace(/^[-•]\s*/, ""));
          } else {
            // Assume it's part of description if it's right after header, else topic
            if (currentModule.topics.length === 0 && !currentModule.description) {
              currentModule.description = trimmed;
            } else {
              currentModule.topics.push(trimmed);
            }
          }
        }
      });

      if (modules.length > 0) {
        onImport(modules);
        setImportText("");
        onOpenChange(false);
        toast.success(`${modules.length} módulos importados correctamente`);
      } else {
        // Fallback: Treat whole text as one module
        onImport([
          {
            title: "Módulo Generado",
            description: importText,
            topics: [],
          },
        ]);
        setImportText("");
        onOpenChange(false);
        toast.success("Módulo generado correctamente");
      }
    } catch (e) {
      console.error(e);
      toast.error("Error al importar el texto");
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            Importación Inteligente
          </DialogTitle>
          <DialogDescription>
            Pega tu temario o índice aquí. La IA detectará automáticamente módulos y lecciones.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="import-area">Contenido del Curso</Label>
              <span className="text-xs text-muted-foreground">
                Soporta formato: &quot;Semana 1: Título&quot;
              </span>
            </div>
            <Textarea
              id="import-area"
              placeholder={`Semana 1: Fundamentos\n- Mentalidad\n- Configuración\n\nSemana 2: Estrategia\n- Avatar\n- Oferta`}
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              className="min-h-[200px] font-mono text-sm"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            onClick={handleSmartImport}
            disabled={!importText.trim() || isImporting}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {isImporting ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                Procesando...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Estructurar Contenido
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
