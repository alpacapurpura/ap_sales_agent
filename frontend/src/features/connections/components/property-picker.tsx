"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi, GA4Property } from "@/lib/api/connections";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle, Globe, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

interface PropertyPickerProps {
  /** Properties returned from OAuth callback or /properties endpoint */
  properties: GA4Property[];
  /** Called after successful property selection */
  onSelected: () => void;
  /** If true, shows as "change" mode instead of initial selection */
  isChangeMode?: boolean;
}

export function PropertyPicker({ properties, onSelected, isChangeMode = false }: PropertyPickerProps) {
  const { getToken } = useAuth();
  const [selectedId, setSelectedId] = useState<string>(
    properties.length === 1 ? properties[0].property_id : ""
  );
  const [manualId, setManualId] = useState("");
  const [showManual, setShowManual] = useState(properties.length === 0);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    const propertyId = showManual ? manualId.trim() : selectedId;
    if (!propertyId) {
      toast.error("Selecciona o ingresa una propiedad");
      return;
    }

    try {
      setSaving(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.selectGoogleAnalyticsProperty(propertyId, token);

      const name = properties.find((p) => p.property_id === propertyId)?.display_name || propertyId;
      toast.success(`Propiedad "${name}" configurada`);
      onSelected();
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al guardar la propiedad");
    } finally {
      setSaving(false);
    }
  };

  // Auto-select if single property and not in change mode
  const autoSelected = properties.length === 1 && !isChangeMode;

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-sm font-medium">
          {isChangeMode ? "Cambiar propiedad GA4" : "Selecciona tu propiedad de Google Analytics"}
        </Label>
        <p className="text-xs text-muted-foreground">
          {properties.length > 0
            ? "Elige cual sitio web quieres monitorear."
            : "No encontramos propiedades en tu cuenta. Puedes ingresar el ID manualmente."}
        </p>
      </div>

      {!showManual && properties.length > 0 ? (
        <div className="space-y-3">
          <Select value={selectedId} onValueChange={setSelectedId}>
            <SelectTrigger>
              <SelectValue placeholder="Selecciona una propiedad..." />
            </SelectTrigger>
            <SelectContent>
              {properties.map((prop) => (
                <SelectItem key={prop.property_id} value={prop.property_id}>
                  <div className="flex items-center gap-2">
                    <Globe className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span>{prop.display_name}</span>
                    {prop.account_name && (
                      <span className="text-muted-foreground text-xs">— {prop.account_name}</span>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {autoSelected && (
            <Alert className="bg-green-50 text-green-800 border-green-200 dark:bg-green-950/30 dark:text-green-200 dark:border-green-800">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                Detectamos tu propiedad automaticamente: <strong>{properties[0].display_name}</strong>
              </AlertDescription>
            </Alert>
          )}

          <button
            type="button"
            onClick={() => setShowManual(true)}
            className="text-xs text-muted-foreground underline hover:text-foreground"
          >
            Ingresar ID manualmente
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <Alert className="bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-800">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Ingresa el Property ID numerico de GA4. Lo encuentras en Google Analytics → Admin → Configuracion de la propiedad.
            </AlertDescription>
          </Alert>

          <Input
            placeholder="Ej: 123456789"
            value={manualId}
            onChange={(e) => setManualId(e.target.value)}
          />

          {properties.length > 0 && (
            <button
              type="button"
              onClick={() => setShowManual(false)}
              className="text-xs text-muted-foreground underline hover:text-foreground"
            >
              Volver a la lista
            </button>
          )}
        </div>
      )}

      <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
        {saving ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <CheckCircle className="mr-2 h-4 w-4" />
        )}
        {isChangeMode ? "Cambiar propiedad" : "Confirmar"}
      </Button>
    </div>
  );
}
