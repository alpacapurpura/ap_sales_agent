"use client";

import { PlusCircle, Download, Settings, RefreshCw } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

interface ActionPanelProps {
  isOpen: boolean;
  onClose: () => void;
  sectionTitle?: string;
}

/**
 *
 */
export function ActionPanel({ isOpen, onClose, sectionTitle }: ActionPanelProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleAction = (action: string) => {
    setIsLoading(true);
    // Simulate async action
    setTimeout(() => {
      setIsLoading(false);
      console.log(`Action executed: ${action} for ${sectionTitle}`);
      onClose();
    }, 1000);
  };

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Gestión de Atracción</SheetTitle>
          <SheetDescription>
            {sectionTitle
              ? `Configuración para ${sectionTitle}`
              : "Acciones generales para el módulo de atracción"}
          </SheetDescription>
        </SheetHeader>

        <div className="py-6 space-y-6">
          {/* Quick Actions */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium leading-none">Acciones Rápidas</h4>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                className="h-20 flex flex-col gap-2"
                onClick={() => handleAction("connect")}
              >
                <PlusCircle className="h-5 w-5" />
                <span>Conectar Canal</span>
              </Button>
              <Button
                variant="outline"
                className="h-20 flex flex-col gap-2"
                onClick={() => handleAction("export")}
              >
                <Download className="h-5 w-5" />
                <span>Exportar Reporte</span>
              </Button>
            </div>
          </div>

          <Separator />

          {/* Configuration Form Mock */}
          <div className="space-y-4">
            <h4 className="text-sm font-medium leading-none">Configuración de Objetivos</h4>
            <div className="grid gap-2">
              <Label htmlFor="target-visitors">Meta de Visitantes Mensuales</Label>
              <Input
                id="target-visitors"
                type="number"
                placeholder="Ej. 10,000"
                defaultValue="5000"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="budget">Presupuesto Máximo (USD)</Label>
              <Input id="budget" type="number" placeholder="Ej. 500" defaultValue="1000" />
            </div>
            <Button
              className="w-full"
              onClick={() => handleAction("save_config")}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                "Guardar Cambios"
              )}
            </Button>
          </div>

          <Separator />

          {/* Advanced Settings */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium leading-none text-muted-foreground">
              Zona Avanzada
            </h4>
            <Button
              variant="ghost"
              className="w-full justify-start text-muted-foreground hover:text-destructive"
              onClick={() => handleAction("reset")}
            >
              <Settings className="mr-2 h-4 w-4" />
              Restablecer configuración por defecto
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
