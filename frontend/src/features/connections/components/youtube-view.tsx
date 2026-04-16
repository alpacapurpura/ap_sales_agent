"use client";

import { useAuth } from "@clerk/nextjs";
import {
  Loader2,
  CheckCircle,
  Youtube,
  Trash2,
  ExternalLink,
  Activity,
  Settings,
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useGoogleOAuthListener } from "@/features/connections/hooks/use-google-oauth-listener";
import { openOAuthPopup } from "@/features/connections/utils/open-oauth-popup";
import { connectionsApi } from "@/lib/api/connections";

import type { YoutubeStatusResponse, TestResponse } from "@/lib/api/connections";

// eslint-disable-next-line sonarjs/cognitive-complexity -- Irreducible: component has 3 render paths (loading → config form → not connected → connected) each guarded by nested conditions. Handlers share OAuth state that would need prop drilling or context to split.
export function YoutubeView() {
  const { getToken } = useAuth();

  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<YoutubeStatusResponse | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResponse | null>(null);

  // Configuration State
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [savingConfig, setSavingConfig] = useState(false);
  const [showConfigForm, setShowConfigForm] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getYoutubeStatus(token);
      setStatus(data);
      // If not configured, show form by default
      if (!data.is_configured) {
        setShowConfigForm(true);
      }
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de YouTube");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clientId || !clientSecret) {
      toast.error("Ingresa Client ID y Secret");
      return;
    }
    try {
      setSavingConfig(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.configureYoutube(token, clientId, clientSecret);
      toast.success("Configuración guardada");
      setShowConfigForm(false);
      await fetchStatus();
    } catch (error: unknown) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "Error al guardar configuración");
    } finally {
      setSavingConfig(false);
    }
  };

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

        toast.info("Finalizando conexión con YouTube...");

        // Use the callback route as redirect URI
        const redirectUri = `${window.location.origin}/connections`;

        await connectionsApi.connectYoutube(code, token, redirectUri);
        toast.success("YouTube conectado exitosamente");

        await fetchStatus();
      } catch (error: unknown) {
        console.error(error);
        toast.error(error instanceof Error ? error.message : "Error al conectar YouTube");
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

      // Use the dedicated callback route
      const redirectUri = `${window.location.origin}/connections`;
      const { url } = await connectionsApi.getYoutubeAuthUrl(token, redirectUri);

      openOAuthPopup({ url, name: "YoutubeAuth" });

      setTimeout(() => setConnecting(false), 60000); // 1 min timeout
    } catch (error: unknown) {
      console.error(error);
      toast.error("No se pudo iniciar la conexión");
      setConnecting(false);
    }
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const token = await getToken();
      if (!token) return;

      const res = await connectionsApi.testYoutube(token);
      setTestResult(res);
      toast.success("Prueba de conexión exitosa");
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Error en la prueba";
      console.error(error);
      toast.error(message);
      setTestResult({ status: "error", message });
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      setDisconnecting(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.disconnectYoutube(token);
      toast.success("YouTube desconectado");
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
    if (!status?.is_configured || showConfigForm) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Youtube className="h-6 w-6 text-red-600" />
              Configurar YouTube App
            </CardTitle>
            <CardDescription>
              Para conectar YouTube, necesitas configurar una App en Google Cloud Console.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveConfig} className="space-y-4">
              <Alert className="bg-amber-50 text-amber-800 border-amber-200">
                <ExternalLink className="h-4 w-4" />
                <AlertTitle>Requisitos Previos</AlertTitle>
                <AlertDescription className="text-xs">
                  1. Crea un proyecto en{" "}
                  <a
                    href="https://console.cloud.google.com/"
                    target="_blank"
                    className="underline font-medium"
                  >
                    Google Cloud Console
                  </a>
                  .
                  <br />
                  2. Habilita la <strong>YouTube Data API v3</strong>.
                  <br />
                  3. Configura la pantalla de consentimiento OAuth (User Type: External).
                  <br />
                  4. Crea credenciales OAuth 2.0.
                  <br />
                  5. Agrega esta URL a Orígenes de JavaScript autorizados:{" "}
                  <code className="bg-amber-100 px-1 rounded">
                    {typeof window !== "undefined" ? window.location.origin : ""}
                  </code>
                  <br />
                  6. Agrega esta URL a URI de redireccionamiento autorizados:{" "}
                  <code className="bg-amber-100 px-1 rounded">
                    {typeof window !== "undefined" ? `${window.location.origin}/connections` : ""}
                  </code>
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="clientId">Client ID</Label>
                <Input
                  id="clientId"
                  placeholder="xxx.apps.googleusercontent.com"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="clientSecret">Client Secret</Label>
                <Input
                  id="clientSecret"
                  type="password"
                  placeholder="GOCSPX-..."
                  value={clientSecret}
                  onChange={(e) => setClientSecret(e.target.value)}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                {status?.is_configured && (
                  <Button type="button" variant="outline" onClick={() => setShowConfigForm(false)}>
                    Cancelar
                  </Button>
                )}
                <Button type="submit" disabled={savingConfig}>
                  {savingConfig ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    "Guardar Configuración"
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Youtube className="h-6 w-6 text-red-600" />
            Conectar YouTube
          </CardTitle>
          <CardDescription>
            Vincula tu canal de YouTube para analizar métricas y comentarios.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Alert className="bg-blue-50 text-blue-800 border-blue-200">
            <ExternalLink className="h-4 w-4" />
            <AlertTitle>Permisos de Lectura</AlertTitle>
            <AlertDescription>
              Solo solicitamos acceso de lectura para obtener estadísticas de tu canal.
            </AlertDescription>
          </Alert>
          <div className="text-sm text-muted-foreground">
            <p>Al conectar, permitirás que el sistema:</p>
            <ul className="list-disc list-inside mt-2 space-y-1 ml-2">
              <li>Leer información básica de tu canal.</li>
              <li>Obtener estadísticas de visualizaciones y suscriptores.</li>
            </ul>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="ghost" size="sm" onClick={() => setShowConfigForm(true)}>
            <Settings className="mr-2 h-4 w-4" />
            Configurar App
          </Button>
          <Button
            onClick={handleConnect}
            disabled={connecting}
            className="bg-red-600 hover:bg-red-700"
          >
            {connecting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Youtube className="mr-2 h-4 w-4" />
            )}
            Conectar con YouTube
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
              <Youtube className="h-6 w-6 text-red-600" />
              YouTube Conectado
            </div>
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
              <CheckCircle className="h-4 w-4" />
              Activo
            </div>
          </CardTitle>
          <CardDescription>Tu canal de YouTube está conectado y sincronizado.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-1">
            <span className="text-muted-foreground text-xs uppercase tracking-wider">
              Canal Conectado
            </span>
            <p className="font-medium text-lg flex items-center gap-2">
              {status.channel_title || "Canal de YouTube"}
              {status.channel_id && (
                <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground font-normal">
                  {status.channel_id}
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
                {testResult.data &&
                  (() => {
                    const ch = testResult.data as {
                      title?: string;
                      statistics?: { viewCount?: string; subscriberCount?: string };
                    };
                    return (
                      <div className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50 grid gap-1">
                        <div>
                          <strong>Título:</strong> {ch.title}
                        </div>
                        <div>
                          <strong>Vistas:</strong> {ch.statistics?.viewCount}
                        </div>
                        <div>
                          <strong>Suscriptores:</strong> {ch.statistics?.subscriberCount}
                        </div>
                      </div>
                    );
                  })()}
              </AlertDescription>
            </Alert>
          )}
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
                <DialogTitle>¿Desvincular YouTube?</DialogTitle>
                <DialogDescription>
                  El sistema dejará de tener acceso a las estadísticas de tu canal.
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
