"use client";

import { useState, useEffect, useCallback } from "react";
import { useGoogleOAuthListener } from "@/features/connections/hooks/use-google-oauth-listener";
import { openOAuthPopup } from "@/features/connections/utils/open-oauth-popup";
import { useAuth } from "@clerk/nextjs";
import {
  connectionsApi,
  GA4Property,
  GoogleAnalyticsStatusResponse,
  TestResponse,
} from "@/lib/api/connections";
import { PropertyPicker } from "@/features/connections/components/property-picker";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
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
  Activity,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// ─── Types ───────────────────────────────────────────────────────────────────

type ServiceKey = "gmail" | "calendar" | "analytics" | "youtube" | "youtube_analytics";

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
        isActive ? "border-border bg-card" : "border-border/50 bg-muted/30",
      )}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border",
          isActive ? "bg-background" : "bg-muted",
        )}
      >
        <Icon className={cn("h-5 w-5", definition.iconColor)} />
      </div>

      <div className="flex-1 space-y-0.5">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{definition.label}</span>
          {isActive && (
            <Badge
              variant="secondary"
              className="text-[10px] px-1.5 py-0 text-green-700 bg-green-100 border-green-200"
            >
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
          Conectas tu cuenta una vez y luego activas o desactivas cada servicio de forma individual
          desde este panel — sin logueos adicionales.
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
        Puedes desactivar servicios individuales en cualquier momento desde este panel sin necesidad
        de revocar tu cuenta completa.
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
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResponse | null>(null);

  // GA4 Property Picker State
  const [gaStatus, setGaStatus] = useState<GoogleAnalyticsStatusResponse | null>(null);
  const [ga4Properties, setGa4Properties] = useState<GA4Property[]>([]);
  const [showGaPropertyPicker, setShowGaPropertyPicker] = useState(false);
  const [loadingGaProperties, setLoadingGaProperties] = useState(false);

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
  useGoogleOAuthListener({
    onSuccess: async (code) => {
      try {
        setIsConnecting(true);
        const token = await getToken();
        if (!token) return;

        toast.info("Conectando tu cuenta de Google...");
        await connectionsApi.connectGoogleWorkspace(code, token);
        toast.success("Google Workspace conectado. Todos los servicios están activos.");

        await fetchStatus();

        // Check if GA needs property selection
        try {
          const gaData = await connectionsApi.getGoogleAnalyticsStatus(token!);
          setGaStatus(gaData);
          if (gaData.is_connected && !gaData.selected_property) {
            const wsResult = await connectionsApi.getGoogleAnalyticsProperties(token!);
            setGa4Properties(wsResult);
            setShowGaPropertyPicker(true);
          }
        } catch (e) {
          console.error("Could not check GA status after workspace connect", e);
        }
      } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Error al conectar Google");
      } finally {
        setIsConnecting(false);
      }
    },
    onError: () => {
      toast.error("Error en autenticación de Google");
      setIsConnecting(false);
    },
  });

  const handleTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const token = await getToken();
      if (!token) return;

      const res = await connectionsApi.testGoogleWorkspace(token);
      setTestResult(res);
      if (res.status === "active") {
        toast.success("Todos los servicios de Google funcionan correctamente");
      } else if (res.status === "partial") {
        toast.warning("Algunos servicios presentan errores");
      } else {
        toast.error(res.message);
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Error en la prueba";
      console.error(error);
      toast.error(message);
      setTestResult({ status: "error", message });
    } finally {
      setTesting(false);
    }
  };

  const handleConnect = async () => {
    try {
      setIsConnecting(true);
      const token = await getToken();
      if (!token) return;

      const { url } = await connectionsApi.getGoogleWorkspaceAuthUrl(token);

      openOAuthPopup({ url, name: "GoogleWorkspaceAuth" });

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
          : prev,
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

  // Check GA property status when workspace is connected
  useEffect(() => {
    if (status?.is_connected) {
      const checkGa = async () => {
        try {
          const token = await getToken();
          if (!token) return;
          const gaData = await connectionsApi.getGoogleAnalyticsStatus(token);
          setGaStatus(gaData);
        } catch (e) {
          // Silently ignore — GA status is supplementary
        }
      };
      checkGa();
    }
  }, [status?.is_connected]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleChangeGaProperty = async () => {
    try {
      setLoadingGaProperties(true);
      const token = await getToken();
      if (!token) return;
      const props = await connectionsApi.getGoogleAnalyticsProperties(token);
      setGa4Properties(props);
      setShowGaPropertyPicker(true);
    } catch (error: any) {
      console.error(error);
      toast.error("Error al obtener propiedades de GA4");
      setGa4Properties([]);
      setShowGaPropertyPicker(true);
    } finally {
      setLoadingGaProperties(false);
    }
  };

  const handleGaPropertySelected = async () => {
    setShowGaPropertyPicker(false);
    const token = await getToken();
    if (token) {
      const gaData = await connectionsApi.getGoogleAnalyticsStatus(token);
      setGaStatus(gaData);
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
                  Cuenta: <span className="font-medium text-foreground">{status.email}</span>
                </>
              ) : (
                "Tu cuenta de Google está activa."
              )}
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button variant="outline" size="sm" onClick={handleTest} disabled={testing}>
              {testing ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Activity className="mr-1.5 h-4 w-4" />
              )}
              Probar Conexión
            </Button>
            <Dialog>
              <DialogTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive"
                >
                  <Unlink className="mr-1.5 h-4 w-4" />
                  Desvincular
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>¿Desvincular Google Workspace?</DialogTitle>
                  <DialogDescription>
                    Se desactivarán todos los servicios de Google: Gmail, Calendar, Analytics y
                    YouTube. Las citas y correos existentes no se eliminarán.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button variant="outline" onClick={() => {}}>
                    Cancelar
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleDisconnectAll}
                    disabled={isDisconnecting}
                  >
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
        </div>
      </CardHeader>

      {/* Test Connection Result */}
      {testResult && (
        <div className="px-6 pb-2">
          <Alert
            variant={testResult.status === "active" ? "default" : "destructive"}
            className={cn(
              testResult.status === "active" &&
                "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20",
              testResult.status === "partial" &&
                "bg-amber-500/15 text-amber-700 border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20",
            )}
          >
            {testResult.status === "active" ? (
              <CheckCircle className="h-4 w-4" />
            ) : testResult.status === "partial" ? (
              <AlertTriangle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <AlertTitle>
              {testResult.status === "active"
                ? "Conexión Estable"
                : testResult.status === "partial"
                  ? "Conexión Parcial"
                  : testResult.status === "auth_error"
                    ? "Credenciales Inválidas"
                    : "Error de Conexión"}
            </AlertTitle>
            <AlertDescription className="space-y-2">
              <p>{testResult.message}</p>
              {testResult.details && (
                <div className="mt-2 space-y-1.5">
                  {Object.entries(testResult.details).map(([service, result]) => (
                    <div key={service} className="text-xs flex items-start gap-2">
                      <span className="font-medium min-w-[70px]">{service}:</span>
                      {result.status === "ok" ? (
                        <span className="text-green-700 dark:text-green-400">
                          OK — {JSON.stringify(result.data, null, 0).slice(0, 120)}
                        </span>
                      ) : result.status === "skipped" ? (
                        <span className="text-muted-foreground">{result.reason}</span>
                      ) : (
                        <span className="text-red-700 dark:text-red-400">{result.error}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </AlertDescription>
          </Alert>
        </div>
      )}

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

        {/* GA4 Property Picker */}
        {showGaPropertyPicker && (
          <>
            <Separator className="my-4" />
            <PropertyPicker
              properties={ga4Properties}
              onSelected={handleGaPropertySelected}
              isChangeMode={!!gaStatus?.selected_property}
            />
          </>
        )}

        {/* GA4 Property Status (when connected but picker not open) */}
        {!showGaPropertyPicker && gaStatus?.is_connected && !gaStatus?.selected_property && (
          <>
            <Separator className="my-4" />
            <Alert className="bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-200 dark:border-amber-800">
              <BarChart className="h-4 w-4" />
              <AlertDescription className="text-xs">
                Google Analytics esta conectado pero falta seleccionar una propiedad.{" "}
                <button
                  type="button"
                  onClick={handleChangeGaProperty}
                  className="underline font-medium hover:text-foreground"
                >
                  Seleccionar ahora
                </button>
              </AlertDescription>
            </Alert>
          </>
        )}

        {!showGaPropertyPicker && gaStatus?.selected_property && (
          <>
            <Separator className="my-4" />
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">
                GA4:{" "}
                <strong className="text-foreground">
                  {gaStatus.selected_property.display_name}
                </strong>
              </span>
              <button
                type="button"
                onClick={handleChangeGaProperty}
                disabled={loadingGaProperties}
                className="text-muted-foreground underline hover:text-foreground"
              >
                {loadingGaProperties ? "Cargando..." : "Cambiar"}
              </button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
