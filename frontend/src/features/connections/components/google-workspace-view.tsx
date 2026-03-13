"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi } from "@/lib/api/connections";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Loader2,
  CheckCircle,
  Mail,
  Calendar,
  BarChart,
  Youtube,
  LogIn,
  Unlink,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// ─── Types ───────────────────────────────────────────────────────────────────

type ServiceKey = "gmail" | "calendar" | "analytics" | "youtube";

interface ServiceStatus {
  is_active: boolean;
  has_credentials: boolean;
}

interface WorkspaceStatus {
  is_connected: boolean;
  email?: string;
  services: Record<ServiceKey, ServiceStatus>;
}

// ─── Static service definitions ──────────────────────────────────────────────

interface ServiceDefinition {
  key: ServiceKey;
  label: string;
  description: string;
  icon: React.ElementType;
  iconColor: string;
  permissions: string[];
}

const SERVICES: ServiceDefinition[] = [
  {
    key: "gmail",
    label: "Gmail",
    description: "Envío de confirmaciones de reserva y notificaciones automáticas.",
    icon: Mail,
    iconColor: "text-red-500",
    permissions: ["Enviar correos en tu nombre", "Leer tu dirección de correo"],
  },
  {
    key: "calendar",
    label: "Google Calendar",
    description: "Agenda citas, verifica disponibilidad y crea Meet automáticamente.",
    icon: Calendar,
    iconColor: "text-blue-500",
    permissions: ["Ver y crear eventos en tu calendario", "Gestionar Google Meet"],
  },
  {
    key: "analytics",
    label: "Google Analytics",
    description: "Métricas de tráfico y conversión de tus propiedades GA4.",
    icon: BarChart,
    iconColor: "text-orange-500",
    permissions: ["Leer métricas y reportes de GA4"],
  },
  {
    key: "youtube",
    label: "YouTube",
    description: "Información básica de tu canal: datos, suscriptores y videos.",
    icon: Youtube,
    iconColor: "text-red-600",
    permissions: ["Leer información básica de tu canal"],
  },
  {
    key: "youtube_analytics",
    label: "YouTube Analytics",
    description: "Métricas avanzadas del podcast: watch time, audiencia, demografía e ingresos.",
    icon: BarChart,
    iconColor: "text-red-500",
    permissions: ["Ver reportes de rendimiento", "Ver datos de ingresos y monetización"],
  },
];

// ─── Sub-components (defined outside to avoid remounts) ──────────────────────

interface ServiceCardProps {
  definition: ServiceDefinition;
  status: ServiceStatus | undefined;
  isToggling: boolean;
  onToggle: (key: ServiceKey, value: boolean) => void;
}

const ServiceCard = ({ definition, status, isToggling, onToggle }: ServiceCardProps) => {
  const Icon = definition.icon;
  const hasCredentials = status?.has_credentials ?? false;
  const isActive = status?.is_active ?? false;

  return (
    <div
      className={cn(
        "flex items-start gap-4 rounded-lg border p-4 transition-colors",
        isActive ? "border-border bg-card" : "border-border/50 bg-muted/30"
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border",
          isActive ? "bg-background" : "bg-muted"
        )}
      >
        <Icon className={cn("h-5 w-5", definition.iconColor)} />
      </div>

      <div className="flex-1 space-y-0.5">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{definition.label}</span>
          {isActive && (
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200">
              Activo
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">{definition.description}</p>
      </div>

      <Switch
        checked={isActive}
        disabled={isToggling || !hasCredentials}
        onCheckedChange={(checked) => onToggle(definition.key, checked)}
        aria-label={`Activar ${definition.label}`}
      />
    </div>
  );
};

interface PreConsentScreenProps {
  onConnect: () => void;
  isConnecting: boolean;
}

const PreConsentScreen = ({ onConnect, isConnecting }: PreConsentScreenProps) => (
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-blue-500" />
        Conectar Google Workspace
      </CardTitle>
      <CardDescription>
        Vincula tu cuenta de Google una sola vez para habilitar todos los servicios.
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <Alert className="bg-blue-50 text-blue-900 border-blue-200 dark:bg-blue-950/30 dark:text-blue-200 dark:border-blue-800">
        <ShieldCheck className="h-4 w-4" />
        <AlertTitle className="text-sm font-semibold">Un solo login, control total</AlertTitle>
        <AlertDescription className="text-xs mt-1">
          Conectas tu cuenta una vez y luego activas o desactivas cada servicio de forma individual desde este panel — sin logueos adicionales.
        </AlertDescription>
      </Alert>

      <div className="space-y-2">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
          Al conectar solicitaremos acceso para:
        </p>
        <div className="grid gap-2">
          {SERVICES.map((svc) => {
            const Icon = svc.icon;
            return (
              <div key={svc.key} className="flex items-start gap-3 text-sm">
                <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", svc.iconColor)} />
                <div>
                  <span className="font-medium">{svc.label}:</span>{" "}
                  <span className="text-muted-foreground">{svc.permissions.join(", ")}.</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <p className="text-[11px] text-muted-foreground">
        Puedes desactivar servicios individuales en cualquier momento desde este panel sin necesidad de revocar tu cuenta completa.
      </p>
    </CardContent>
    <CardFooter>
      <Button onClick={onConnect} disabled={isConnecting} className="w-full sm:w-auto">
        {isConnecting ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <LogIn className="mr-2 h-4 w-4" />
        )}
        Continuar con Google
      </Button>
    </CardFooter>
  </Card>
);

// ─── Main Component ───────────────────────────────────────────────────────────

export function GoogleWorkspaceView() {
  const { getToken } = useAuth();

  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<WorkspaceStatus | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);
  const [togglingService, setTogglingService] = useState<ServiceKey | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getGoogleWorkspaceStatus(token);
      setStatus(data as WorkspaceStatus);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar el estado de Google Workspace");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Listen for the OAuth code sent by the popup callback page
  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type !== "GOOGLE_OAUTH_SUCCESS" || !event.data?.code) return;

      try {
        setIsConnecting(true);
        const token = await getToken();
        if (!token) return;

        toast.info("Conectando tu cuenta de Google...");
        await connectionsApi.connectGoogleWorkspace(event.data.code, token);
        toast.success("Google Workspace conectado. Todos los servicios están activos.");

        await fetchStatus();
      } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Error al conectar Google");
      } finally {
        setIsConnecting(false);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [getToken, fetchStatus]);

  const handleConnect = async () => {
    try {
      setIsConnecting(true);
      const token = await getToken();
      if (!token) return;

      const { url } = await connectionsApi.getGoogleWorkspaceAuthUrl(token);

      const width = 520;
      const height = 640;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;

      window.open(
        url,
        "GoogleWorkspaceAuth",
        `width=${width},height=${height},top=${top},left=${left},toolbar=no,menubar=no,scrollbars=yes,resizable=yes,location=no,status=no`
      );

      // Safety timeout: reset button if popup is closed without completing
      setTimeout(() => setIsConnecting(false), 90_000);
    } catch (error: any) {
      console.error(error);
      toast.error("No se pudo iniciar la conexión con Google");
      setIsConnecting(false);
    }
  };

  const handleToggleService = async (serviceKey: ServiceKey, isActive: boolean) => {
    try {
      setTogglingService(serviceKey);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.toggleGoogleWorkspaceService(serviceKey, isActive, token);

      const svcLabel = SERVICES.find((s) => s.key === serviceKey)?.label ?? serviceKey;
      toast.success(isActive ? `${svcLabel} activado` : `${svcLabel} desactivado`);

      // Optimistic update
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              services: {
                ...prev.services,
                [serviceKey]: { ...prev.services[serviceKey], is_active: isActive },
              },
            }
          : prev
      );
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al actualizar el servicio");
      await fetchStatus(); // Re-sync on error
    } finally {
      setTogglingService(null);
    }
  };

  const handleDisconnectAll = async () => {
    try {
      setIsDisconnecting(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.disconnectGoogleWorkspace(token);
      toast.success("Cuenta de Google desvinculada");
      await fetchStatus();
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al desconectar");
    } finally {
      setIsDisconnecting(false);
    }
  };

  // ── Loading ──
  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // ── Not connected: show pre-consent screen ──
  if (!status?.is_connected) {
    return <PreConsentScreen onConnect={handleConnect} isConnecting={isConnecting} />;
  }

  // ── Connected: show workspace hub ──
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Google Workspace Conectado
            </CardTitle>
            <CardDescription className="mt-1">
              {status.email ? (
                <>
                  Cuenta:{" "}
                  <span className="font-medium text-foreground">{status.email}</span>
                </>
              ) : (
                "Tu cuenta de Google está activa."
              )}
            </CardDescription>
          </div>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-destructive shrink-0">
                <Unlink className="mr-1.5 h-4 w-4" />
                Desvincular
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>¿Desvincular Google Workspace?</DialogTitle>
                <DialogDescription>
                  Se desactivarán todos los servicios de Google: Gmail, Calendar, Analytics y YouTube. Las citas y correos existentes no se eliminarán.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => {}}>
                  Cancelar
                </Button>
                <Button variant="destructive" onClick={handleDisconnectAll} disabled={isDisconnecting}>
                  {isDisconnecting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    "Sí, desvincular todo"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="pt-5 space-y-3">
        <p className="text-xs text-muted-foreground">
          Activa o desactiva individualmente qué servicios de Google puede usar la plataforma.
        </p>

        {SERVICES.map((svc) => (
          <ServiceCard
            key={svc.key}
            definition={svc}
            status={status.services[svc.key]}
            isToggling={togglingService === svc.key}
            onToggle={handleToggleService}
          />
        ))}
      </CardContent>
    </Card>
  );
}
