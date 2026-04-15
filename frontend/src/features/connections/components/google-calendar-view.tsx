"use client";

import { useAuth } from "@clerk/nextjs";
import {
  Loader2,
  CheckCircle,
  Calendar,
  Trash2,
  ExternalLink,
  Copy,
  Link as LinkIcon,
  Activity,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useGoogleOAuthListener } from "@/features/connections/hooks/use-google-oauth-listener";
import { openOAuthPopup } from "@/features/connections/utils/open-oauth-popup";
import { connectionsApi } from "@/lib/api/connections";

import type { TestResponse } from "@/lib/api/connections";

export function GoogleCalendarView() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<{
    is_connected: boolean;
    email?: string;
    booking_link?: string;
  } | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [generatingLink, setGeneratingLink] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResponse | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getCalendarStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Calendario");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  // Handle OAuth Callback (Popup Listener)
  useGoogleOAuthListener({
    onSuccess: async (code) => {
      try {
        setConnecting(true);
        const token = await getToken();
        if (!token) return;

        toast.info("Finalizando conexión con Google...");

        // Must match the redirect URI registered in Google Cloud Console
        const redirectUri = `${window.location.origin}/connections/google/callback`;

        await connectionsApi.connectGoogle(code, token, redirectUri);
        toast.success("Google Calendar conectado exitosamente");

        await fetchStatus();
      } catch (error: unknown) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "Error al conectar Google Calendar");
      } finally {
        setConnecting(false);
      }
    },
    onError: () => {
      toast.error("Error en autenticación de Google");
      setConnecting(false);
    },
  });

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;

      // Must match the redirect URI registered in Google Cloud Console
      const redirectUri = `${window.location.origin}/connections/google/callback`;
      const { url } = await connectionsApi.getGoogleAuthUrl(token, redirectUri);

      openOAuthPopup({ url, name: "GoogleCalendarAuth" });

      // We don't setConnecting(false) here, we wait for the message or user to close
      // But since we can't easily detect close without polling, we might want to reset if it takes too long
      // For now, let's leave it as is or add a timeout?
      // Better UX: keep it loading until message received.
      // If user closes popup manually, button stays 'loading'.
      // Let's add a simple focus listener to reset if needed?
      // Or just let user click again (but button is disabled).
      // Let's add a timeout for safety.
      setTimeout(() => setConnecting(false), 60000); // 1 min timeout
    } catch (error: unknown) {
      console.error(error);
      toast.error("No se pudo iniciar la conexión");
      setConnecting(false);
    }
  };

  const handleGenerateLink = async () => {
    try {
      setGeneratingLink(true);
      const token = await getToken();
      if (!token) return;

      const res = await connectionsApi.generateBookingLink(token);
      toast.success("Enlace generado correctamente");
      // Update status with new link
      setStatus((prev) => (prev ? { ...prev, booking_link: res.url } : null));
    } catch (error: unknown) {
      toast.error("Error generando enlace");
    } finally {
      setGeneratingLink(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const token = await getToken();
      if (!token) return;

      const res = await connectionsApi.testCalendar(token);
      setTestResult(res);
      toast.success("Prueba de conexión exitosa");
    } catch (error: unknown) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "Error en la prueba");
      setTestResult({
        status: "error",
        message: error instanceof Error ? error.message : "Error desconocido",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setDisconnecting(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.disconnectCalendar(token);
      toast.success("Google Calendar desconectado");
      setStatus({ is_connected: false });
      setTestResult(null);
    } catch (error: unknown) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "Error al desconectar");
    } finally {
      setDisconnecting(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (!status?.is_connected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-6 w-6 text-red-500" />
            Conectar Google Calendar
          </CardTitle>
          <CardDescription>
            Vincula tu cuenta de Google Workspace para gestionar citas y disponibilidad
            automáticamente.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Alert className="bg-blue-50 text-blue-800 border-blue-200">
            <ExternalLink className="h-4 w-4" />
            <AlertTitle>Requisito Google Workspace</AlertTitle>
            <AlertDescription>
              Actualmente solo soportamos cuentas de Google Workspace (Empresariales). Asegúrate de
              tener permisos para instalar aplicaciones.
            </AlertDescription>
          </Alert>
          <div className="text-sm text-muted-foreground">
            <p>Al conectar, permitirás que el sistema:</p>
            <ul className="list-disc list-inside mt-2 space-y-1 ml-2">
              <li>Ver tu disponibilidad (Free/Busy).</li>
              <li>Crear eventos en tu calendario principal.</li>
              <li>Generar enlaces de Google Meet automáticamente.</li>
            </ul>
          </div>
        </CardContent>
        <CardFooter>
          <Button
            onClick={handleConnect}
            disabled={connecting}
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700"
          >
            {connecting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Calendar className="mr-2 h-4 w-4" />
            )}
            Conectar con Google
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="h-6 w-6 text-red-500" />
              Google Calendar Conectado
            </div>
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
              <CheckCircle className="h-4 w-4" />
              Activo
            </div>
          </CardTitle>
          <CardDescription>
            Tu calendario está sincronizado y listo para agendar citas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-1">
            <span className="text-muted-foreground text-xs uppercase tracking-wider">
              Cuenta Conectada
            </span>
            <p className="font-medium text-lg flex items-center gap-2">
              {status.email || "Usuario de Google"}
              {status.email && (
                <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground font-normal">
                  {status.email.split("@")[1]}
                </span>
              )}
            </p>
          </div>

          {testResult && (
            <Alert
              variant={testResult.status === "ok" ? "default" : "destructive"}
              className={
                testResult.status === "ok"
                  ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20"
                  : ""
              }
            >
              <Activity className="h-4 w-4" />
              <AlertTitle>
                {testResult.status === "ok" ? "Conexión Estable" : "Error de Conexión"}
              </AlertTitle>
              <AlertDescription>
                {testResult.message}
                {testResult.data && (
                  <div className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50 grid gap-1">
                    <div>
                      <strong>Email:</strong> {String(testResult.data.email ?? "")}
                    </div>
                    <div>
                      <strong>Busy Slots (24h):</strong> {String(testResult.data.busy_slots ?? "")}
                    </div>
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}

          <div className="pt-4 border-t space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-muted-foreground text-xs uppercase tracking-wider">
                  Enlace de Reservas Público
                </span>
                <p className="text-sm text-muted-foreground">
                  Comparte este enlace para que tus leads agenden citas automáticamente.
                </p>
              </div>
              {!status.booking_link && (
                <Button
                  onClick={handleGenerateLink}
                  disabled={generatingLink}
                  size="sm"
                  variant="outline"
                >
                  {generatingLink ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <LinkIcon className="mr-2 h-4 w-4" />
                  )}
                  Generar Link
                </Button>
              )}
            </div>

            {status.booking_link && (
              <div className="flex items-center gap-2">
                <div className="bg-muted p-2 rounded text-sm font-mono flex-1 overflow-hidden text-ellipsis whitespace-nowrap border">
                  {typeof window !== "undefined" ? window.location.origin : ""}
                  {status.booking_link}
                </div>
                <Button
                  size="icon"
                  variant="secondary"
                  onClick={() => {
                    const url = `${window.location.origin}${status.booking_link}`;
                    void navigator.clipboard.writeText(url);
                    toast.success("Enlace copiado al portapapeles");
                  }}
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" asChild>
                  <a href={status.booking_link} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            )}
          </div>
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row gap-3 justify-between border-t pt-6">
          <Button variant="outline" onClick={handleTest} disabled={testing}>
            {testing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Activity className="mr-2 h-4 w-4" />
            )}
            Probar Conexión
          </Button>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="destructive" disabled={disconnecting}>
                <Trash2 className="mr-2 h-4 w-4" />
                Desconectar
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>¿Desvincular Google Calendar?</DialogTitle>
                <DialogDescription>
                  El sistema dejará de poder verificar tu disponibilidad y agendar nuevas citas. Las
                  citas existentes no se borrarán de tu calendario.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline">Cancelar</Button>
                <Button variant="destructive" onClick={handleDisconnect} disabled={disconnecting}>
                  {disconnecting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    "Sí, desconectar"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardFooter>
      </Card>
    </div>
  );
}
