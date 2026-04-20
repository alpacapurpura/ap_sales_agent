"use client";

import { useAuth } from "@clerk/nextjs";
import {
  Loader2,
  CheckCircle,
  BarChart,
  Trash2,
  ExternalLink,
  Activity,
  Settings,
  Save,
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
import { PropertyPicker } from "@/features/connections/components/PropertyPicker";
import { useGoogleOAuthListener } from "@/features/connections/hooks/use-google-oauth-listener";
import { openOAuthPopup } from "@/features/connections/utils/open-oauth-popup";
import { connectionsApi } from "@/lib/api/connections";

import type {
  GoogleAnalyticsStatusResponse,
  GA4Property,
  TestResponse,
} from "@/lib/api/connections";

/**
 * Complex connection-flow UI with branching state (OAuth, property picker,
 * error screens) — pre-existing complexity exceeds the 15-point budget.
 * Tracked as tech debt; refactor to sub-components in a dedicated sprint.
 */
// eslint-disable-next-line sonarjs/cognitive-complexity
export function GoogleAnalyticsView() {
  const { getToken } = useAuth();

  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<GoogleAnalyticsStatusResponse | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResponse | null>(null);

  // Configuration State
  const [configMode, setConfigMode] = useState(false);
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [savingConfig, setSavingConfig] = useState(false);

  // Property Picker State
  const [properties, setProperties] = useState<GA4Property[]>([]);
  const [showPropertyPicker, setShowPropertyPicker] = useState(false);
  const [loadingProperties, setLoadingProperties] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getGoogleAnalyticsStatus(token);
      setStatus(data);

      if (data && !data.is_configured) {
        setConfigMode(true);
      }
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Google Analytics");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  // Handle OAuth Callback
  useGoogleOAuthListener({
    onSuccess: async (code) => {
      try {
        setConnecting(true);
        const token = await getToken();
        if (!token) return;

        toast.info("Finalizando conexion con Google Analytics...");
        const redirectUri = `${window.location.origin}/connections`;
        const result = await connectionsApi.connectGoogleAnalytics(code, token, redirectUri);

        toast.success("Google Analytics conectado");

        // Show property picker with returned properties
        if (result.properties && result.properties.length > 0) {
          setProperties(result.properties);
          setShowPropertyPicker(true);
        } else {
          // No properties returned — show picker with empty state (manual input)
          setProperties([]);
          setShowPropertyPicker(true);
        }

        await fetchStatus();
      } catch (error: unknown) {
        const message =
          error instanceof Error ? error.message : "Error al conectar Google Analytics";
        console.error(error);
        toast.error(message);
      } finally {
        setConnecting(false);
      }
    },
    onError: () => {
      toast.error("Error en autenticacion de Google");
      setConnecting(false);
    },
  });

  const handleSaveConfig = async () => {
    if (!clientId || !clientSecret) {
      toast.error("Por favor completa todos los campos");
      return;
    }
    try {
      setSavingConfig(true);
      const token = await getToken();
      if (!token) return;
      await connectionsApi.configureGoogleAnalytics(
        { client_id: clientId, client_secret: clientSecret },
        token,
      );
      toast.success("Configuracion guardada exitosamente");
      setConfigMode(false);
      await fetchStatus();
    } catch (error: unknown) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "Error al guardar configuracion");
    } finally {
      setSavingConfig(false);
    }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;
      const redirectUri = `${window.location.origin}/connections`;
      const { url } = await connectionsApi.getGoogleAnalyticsAuthUrl(token, redirectUri);
      openOAuthPopup({ url, name: "GoogleAnalyticsAuth" });
      setTimeout(() => setConnecting(false), 60000);
    } catch (error: unknown) {
      console.error(error);
      toast.error("No se pudo iniciar la conexion. Verifica tu configuracion.");
      setConnecting(false);
    }
  };

  const handleChangeProperty = async () => {
    try {
      setLoadingProperties(true);
      const token = await getToken();
      if (!token) return;
      const props = await connectionsApi.getGoogleAnalyticsProperties(token);
      setProperties(props);
      setShowPropertyPicker(true);
    } catch (error: unknown) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "Error al obtener propiedades");
      // Show picker with empty properties (manual fallback)
      setProperties([]);
      setShowPropertyPicker(true);
    } finally {
      setLoadingProperties(false);
    }
  };

  const handlePropertySelected = () => {
    setShowPropertyPicker(false);
    void fetchStatus();
  };

  const handleTest = async () => {
    try {
      setTesting(true);
      setTestResult(null);
      const token = await getToken();
      if (!token) return;
      const res = await connectionsApi.testGoogleAnalytics(token);
      setTestResult(res);
      toast.success("Prueba de conexion exitosa");
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
      await connectionsApi.disconnectGoogleAnalytics(token);
      toast.success("Google Analytics desconectado");
      setStatus((prev) =>
        prev ? { ...prev, is_connected: false, selected_property: null } : null,
      );
      setTestResult(null);
      setShowPropertyPicker(false);
    } catch (error: unknown) {
      console.error(error);
      toast.error(error instanceof Error ? error.message : "Error al desconectar");
    } finally {
      setDisconnecting(false);
    }
  };

  // -- Loading --
  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // -- Configuration Mode --
  if (configMode) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-6 w-6 text-gray-500" />
            Configuracion de Google Analytics
          </CardTitle>
          <CardDescription>
            Ingresa las credenciales de tu aplicacion Google Cloud (OAuth 2.0 Client ID).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert className="bg-blue-50 text-blue-800 border-blue-200">
            <ExternalLink className="h-4 w-4" />
            <AlertTitle>Instrucciones</AlertTitle>
            <AlertDescription>
              1. Ve a Google Cloud Console.
              <br />
              2. Crea credenciales OAuth 2.0.
              <br />
              3. Anade <code>
                {typeof window !== "undefined" ? window.location.origin : ""}
              </code>{" "}
              como Origen Autorizado.
              <br />
              4. Anade{" "}
              <code>
                {typeof window !== "undefined" ? window.location.origin : ""}/connections
              </code>{" "}
              como URI de redireccion.
            </AlertDescription>
          </Alert>
          <div className="space-y-2">
            <Label htmlFor="client_id">Client ID</Label>
            <Input
              id="client_id"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="apps.googleusercontent.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="client_secret">Client Secret</Label>
            <Input
              id="client_secret"
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="Tu secreto de cliente"
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          {status?.is_configured ? (
            <Button variant="ghost" onClick={() => setConfigMode(false)}>
              Cancelar
            </Button>
          ) : (
            <div></div>
          )}
          <Button onClick={handleSaveConfig} disabled={savingConfig}>
            {savingConfig ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Guardar Configuracion
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // -- Not Connected --
  if (!status?.is_connected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-6 w-6 text-orange-500" />
            Conectar Google Analytics
          </CardTitle>
          <CardDescription>
            Vincula tu cuenta de Google Analytics 4 para ver metricas de trafico y conversion.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Alert className="bg-blue-50 text-blue-800 border-blue-200">
            <ExternalLink className="h-4 w-4" />
            <AlertTitle>Google Analytics 4</AlertTitle>
            <AlertDescription>Soportamos propiedades de Google Analytics 4 (GA4).</AlertDescription>
          </Alert>
          <div className="text-sm text-muted-foreground">
            <p>Al conectar, permitiras que el sistema:</p>
            <ul className="list-disc list-inside mt-2 space-y-1 ml-2">
              <li>Leer propiedades y metricas de GA4.</li>
              <li>Generar reportes de rendimiento.</li>
            </ul>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={() => setConfigMode(true)}>
            <Settings className="mr-2 h-4 w-4" />
            Editar Config
          </Button>
          <Button
            onClick={handleConnect}
            disabled={connecting}
            className="bg-orange-600 hover:bg-orange-700"
          >
            {connecting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <BarChart className="mr-2 h-4 w-4" />
            )}
            Conectar
          </Button>
        </CardFooter>
      </Card>
    );
  }

  // -- Connected but no property selected → Property Picker --
  if (!status.selected_property || showPropertyPicker) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-6 w-6 text-orange-500" />
            {status.selected_property ? "Cambiar propiedad" : "Configura tu propiedad GA4"}
          </CardTitle>
          <CardDescription>
            {status.selected_property
              ? `Actualmente: ${status.selected_property.display_name}`
              : "Un ultimo paso: selecciona que sitio web quieres monitorear."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PropertyPicker
            properties={properties}
            onSelected={handlePropertySelected}
            isChangeMode={!!status.selected_property}
          />
        </CardContent>
      </Card>
    );
  }

  // -- Connected + property selected → Full status --
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart className="h-6 w-6 text-orange-500" />
              Analytics Conectado
            </div>
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
              <CheckCircle className="h-4 w-4" />
              Activo
            </div>
          </CardTitle>
          <CardDescription className="flex items-center gap-1.5">
            Propiedad: <strong>{status.selected_property.display_name}</strong>
            <button
              type="button"
              onClick={handleChangeProperty}
              disabled={loadingProperties}
              className="text-xs text-muted-foreground underline hover:text-foreground ml-1"
            >
              {loadingProperties ? "Cargando..." : "Cambiar"}
            </button>
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
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
                {testResult.status === "ok" ? "Conexion Estable" : "Error de Conexion"}
              </AlertTitle>
              <AlertDescription>
                {testResult.message}
                {testResult.data && Array.isArray(testResult.data) && (
                  <div className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50 max-h-40 overflow-y-auto">
                    <p className="font-semibold mb-1">
                      Cuentas encontradas: {testResult.data.length}
                    </p>
                    <ul className="list-disc pl-4">
                      {(
                        testResult.data as {
                          account?: string;
                          name?: string;
                          displayName?: string;
                        }[]
                      ).map((acc, i: number) => (
                        <li key={i}>
                          {acc.account || acc.name} - {acc.displayName}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row gap-3 justify-between border-t pt-6">
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleTest} disabled={testing}>
              {testing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Activity className="mr-2 h-4 w-4" />
              )}
              Probar
            </Button>
            <Button variant="outline" onClick={() => setConfigMode(true)}>
              <Settings className="h-4 w-4" />
            </Button>
          </div>

          <Dialog>
            <DialogTrigger asChild>
              <Button variant="destructive" disabled={disconnecting}>
                <Trash2 className="mr-2 h-4 w-4" />
                Desconectar
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Desvincular Google Analytics?</DialogTitle>
                <DialogDescription>Dejaras de recibir metricas de esta cuenta.</DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline">Cancelar</Button>
                <Button variant="destructive" onClick={handleDisconnect} disabled={disconnecting}>
                  {disconnecting ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    "Si, desconectar"
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
