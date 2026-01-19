"use client";

import { useState } from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info, GitBranch } from "lucide-react";

interface InheritanceSelectorProps {
  currentMode: "GLOBAL" | "CUSTOM";
  onModeChange: (mode: "GLOBAL" | "CUSTOM") => void;
  globalAvatarName?: string;
}

export function InheritanceSelector({ 
  currentMode, 
  onModeChange,
  globalAvatarName = "Avatar de Marca (Default)"
}: InheritanceSelectorProps) {
  
  return (
    <Card className="bg-muted/30 border-dashed">
      <CardContent className="pt-6">
        <div className="flex flex-col md:flex-row gap-6 justify-between items-start md:items-center">
           <div className="space-y-1">
              <div className="flex items-center gap-2">
                 <GitBranch className="h-4 w-4 text-primary" />
                 <Label className="text-base font-medium">Estrategia de Avatar</Label>
              </div>
              <p className="text-sm text-muted-foreground">
                Define si esta oferta usa la identidad global o una personalidad específica.
              </p>
           </div>

           <div className="flex items-center gap-4 bg-background p-2 rounded-lg border">
              <span className={`text-sm ${currentMode === "GLOBAL" ? "font-medium text-primary" : "text-muted-foreground"}`}>
                Heredar Global
              </span>
              <Switch 
                checked={currentMode === "CUSTOM"}
                onCheckedChange={(chk) => onModeChange(chk ? "CUSTOM" : "GLOBAL")}
              />
              <span className={`text-sm ${currentMode === "CUSTOM" ? "font-medium text-primary" : "text-muted-foreground"}`}>
                Personalizar
              </span>
           </div>
        </div>

        {currentMode === "GLOBAL" && (
           <Alert className="mt-4 bg-blue-50/50 border-blue-200">
              <Info className="h-4 w-4 text-blue-500" />
              <AlertDescription className="text-blue-700 text-sm">
                 Esta oferta usará automáticamente la configuración de <strong>{globalAvatarName}</strong>. 
                 Cualquier cambio en el avatar global se reflejará aquí.
              </AlertDescription>
           </Alert>
        )}
      </CardContent>
    </Card>
  );
}
