"use client";

import { Construction } from "lucide-react";

import { Badge } from "@/components/ui/badge";

export function CloneUpload() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <p className="text-sm text-muted-foreground">
          Sube conversaciones o textos propios para que el agente aprenda tu estilo personal.
        </p>
        <Badge variant="secondary" className="text-xs flex-shrink-0">
          Próximamente
        </Badge>
      </div>

      {/* Drag-and-drop placeholder */}
      <div className="relative rounded-xl border-2 border-dashed border-muted p-10 flex flex-col items-center justify-center gap-4 text-muted-foreground/50">
        <Construction className="w-8 h-8" />
        <div className="text-center">
          <p className="text-sm font-medium">Clonación de personalidad en desarrollo</p>
          <p className="text-xs mt-1">
            Formatos aceptados: .txt, .json (conversaciones exportadas de WhatsApp, IG, Telegram)
          </p>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Cuando esté disponible, podrás arrastrar tus chats exportados y el motor de análisis
        detectará automáticamente tu tono, vocabulario y patrones lingüísticos.
      </p>
    </div>
  );
}
