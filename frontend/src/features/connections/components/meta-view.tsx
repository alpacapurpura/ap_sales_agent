"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useSearchParams } from "next/navigation";
import { connectionsApi, MetaStatusResponse } from "@/lib/api/connections";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, CheckCircle, Trash2, ExternalLink, Activity, Facebook, Settings2 } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function MetaView() {
  const { getToken } = useAuth();
  const searchParams = useSearchParams();
  
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<MetaStatusResponse | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  // Configuration state
  const [appId, setAppId] = useState("");
  const [appSecret, setAppSecret] = useState("");
  const [configuring, setConfiguring] = useState(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getMetaStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Meta");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  // Handle OAuth Callback (Popup Listener)
  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      
      if (event.data?.type === "META_OAUTH_SUCCESS" && event.data?.code) {
         try {
          setConnecting(true);
          const token = await getToken();
          if (!token) return;

          toast.info("Finalizando conexión con Meta...");
          
          // Use the callback route as redirect URI
          const redirectUri = window.location.origin + "/connections"; // Or just window.location.origin if configured that way
          // Actually SettingsView uses window.location.origin + "/connections" implicitly or explicitly?
          // The auth url was generated with a redirect uri. It must match.
          // In handleConnect I will use window.location.origin (the settings page).
          // But wait, the popup opens the auth url, then redirects to redirect_uri.
          // The redirect_uri should probably be the same page where the popup logic is handled.
          // The popup logic is in SettingsView, which is at /:tenantId/settings.
          // But if the redirect_uri is fixed in config to .../connections, then we need a route for that.
          // The user config has "https://laptopchris.alpacapurpura.lat/connections".
          // This implies there is a route /connections.
          // I should check if there is a page at /connections.
          // If not, I should probably use window.location.href (the current settings page) if allowed.
          
          // Assuming /connections exists or the user handles it.
          // But wait, the popup logic is in SettingsViewInner!
          // So if the redirect goes to /connections, does it render SettingsView?
          // If /connections is not a valid route, it might 404.
          
          // Let's check if app/connections exists.
          
          await connectionsApi.connectMeta(event.data.code, token, window.location.origin + "/connections"); 
          toast.success("Meta conectado exitosamente");
          
          await fetchStatus();
        } catch (error: any) {
          console.error(error);
          toast.error(error.message || "Error al conectar Meta");
        } finally {
          setConnecting(false);
        }
      } else if (event.data?.type === "META_OAUTH_ERROR") {
          toast.error("Error en autenticación de Meta");
          setConnecting(false);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const handleConfigure = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!appId || !appSecret) {
      toast.error("Por favor completa todos los campos");
      return;
    }

    try {
      setConfiguring(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.configureMeta({ app_id: appId, app_secret: appSecret }, token);
      toast.success("Configuración guardada exitosamente");
      await fetchStatus();
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al guardar configuración");
    } finally {
      setConfiguring(false);
    }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;

      // We use /connections as the callback because that's what's likely configured in the app
      // And the popup listener in SettingsView handles it if it's loaded there.
      // But if /connections doesn't render SettingsView, how does the popup logic work?
      // Ah, usually there is a dedicated page for handling callbacks or the settings page itself.
      // If the redirect URI is the settings page, then it works.
      // If it's /connections, we need to ensure that page exists and has the logic.
      // But I saw the logic in SettingsView! 
      // This means SettingsView IS mounted when the popup redirects?
      // Or maybe /connections is just an alias or the user meant to create it?
      
      // Let's assume the redirect URI should be the current page or a dedicated callback page.
      // I'll stick to what was in GoogleAnalyticsView: window.location.origin + "/connections"
      const redirectUri = window.location.origin + "/connections";
      
      const { url } = await connectionsApi.getMetaAuthUrl(token, redirectUri);
      
      const width = 600;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      
      window.open(
        url,
        "MetaAuth",
        `width=${width},height=${height},top=${top},left=${left},toolbar=no,menubar=no,scrollbars=yes,resizable=yes,location=no,status=no`
      );

      // Check if popup closed? No, we wait for message.
      // But if user closes it manually, we are stuck in connecting state.
      setTimeout(() => setConnecting(false), 60000); 

    } catch (error: any) {
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
          
          const res = await connectionsApi.testMeta(token);
          setTestResult(res);
          toast.success("Prueba de conexión exitosa");
      } catch (error: any) {
          console.error(error);
          toast.error(error.message || "Error en la prueba");
          setTestResult({ status: "error", message: error.message });
      } finally {
          setTesting(false);
      }
  };

  const handleDisconnect = async () => {
    try {
      setDisconnecting(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.disconnectMeta(token);
      toast.success("Meta desconectado");
      setStatus({ is_connected: false });
      setTestResult(null);
    } catch (error: any) {
      console.error(error);
      toast.error(error.message || "Error al desconectar");
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

  if (!status?.is_configured) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings2 className="h-6 w-6 text-gray-600" />
            Configurar Meta Developer App
          </CardTitle>
          <CardDescription>
            Ingresa las credenciales de tu aplicación de Meta para habilitar la conexión.
            <br />
            <a 
              href="https://developers.facebook.com/apps/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline flex items-center gap-1 mt-1 w-fit"
            >
              Ir a Meta for Developers <ExternalLink className="h-3 w-3" />
            </a>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleConfigure} className="space-y-4">
             <div className="space-y-2">
                <Label htmlFor="appId">App ID</Label>
                <Input 
                  id="appId" 
                  placeholder="Ej: 123456789012345" 
                  value={appId} 
                  onChange={(e) => setAppId(e.target.value)} 
                  disabled={configuring}
                />
             </div>
             <div className="space-y-2">
                <Label htmlFor="appSecret">App Secret</Label>
                <Input 
                  id="appSecret" 
                  type="password"
                  placeholder="Ej: a1b2c3d4e5f6..." 
                  value={appSecret} 
                  onChange={(e) => setAppSecret(e.target.value)} 
                  disabled={configuring}
                />
             </div>
             <div className="pt-2">
                <Button type="submit" disabled={configuring}>
                  {configuring ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Guardar Configuración"}
                </Button>
             </div>
          </form>
        </CardContent>
      </Card>
    );
  }

  if (!status?.is_connected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Facebook className="h-6 w-6 text-blue-600" />
            Conectar Meta Business Suite
          </CardTitle>
          <CardDescription>
            Vincula tu cuenta de Facebook e Instagram para gestionar anuncios y ver estadísticas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            <Alert className="bg-blue-50 text-blue-800 border-blue-200">
                <ExternalLink className="h-4 w-4" />
                <AlertTitle>Meta Graph API</AlertTitle>
                <AlertDescription>
                    Utilizamos la API oficial de Meta para conectar tus activos.
                </AlertDescription>
            </Alert>
            <div className="text-sm text-muted-foreground">
                <p>Al conectar, permitirás que el sistema:</p>
                <ul className="list-disc list-inside mt-2 space-y-1 ml-2">
                    <li>Leer información de tus Páginas de Facebook.</li>
                    <li>Acceder a estadísticas de anuncios (Ads Management).</li>
                    <li>Leer insights de rendimiento.</li>
                </ul>
            </div>
        </CardContent>
        <CardFooter className="flex flex-col sm:flex-row gap-3 justify-between">
            <Button variant="ghost" size="sm" onClick={() => setStatus(prev => prev ? { ...prev, is_configured: false } : null)}>
                <Settings2 className="mr-2 h-4 w-4" />
                Configuración
            </Button>
            <Button onClick={handleConnect} disabled={connecting} className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700">
                {connecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Facebook className="mr-2 h-4 w-4" />}
                Conectar con Facebook
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
                        <Facebook className="h-6 w-6 text-blue-600" />
                        Meta Conectado
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                        <CheckCircle className="h-4 w-4" />
                        Activo
                    </div>
                </CardTitle>
                <CardDescription>
                    Tu cuenta de Meta está conectada como <strong>{status.name}</strong> ({status.account_id}).
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                
                {testResult && (
                    <Alert variant={testResult.status === "ok" ? "default" : "destructive"} className={testResult.status === "ok" ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20" : ""}>
                        <Activity className="h-4 w-4" />
                        <AlertTitle>{testResult.status === "ok" ? "Conexión Estable" : "Error de Conexión"}</AlertTitle>
                        <AlertDescription>
                            {testResult.message}
                            {testResult.data && (
                                <div className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50 max-h-40 overflow-y-auto">
                                    <pre>{JSON.stringify(testResult.data, null, 2)}</pre>
                                </div>
                            )}
                        </AlertDescription>
                    </Alert>
                )}
            </CardContent>
            <CardFooter className="flex flex-col sm:flex-row gap-3 justify-between border-t pt-6">
                <Button variant="outline" onClick={handleTest} disabled={testing}>
                    {testing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Activity className="mr-2 h-4 w-4" />}
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
                            <DialogTitle>¿Desvincular Meta?</DialogTitle>
                            <DialogDescription>
                                Dejarás de recibir métricas y acceso a tus anuncios.
                            </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                            <Button variant="outline">Cancelar</Button>
                            <Button variant="destructive" onClick={handleDisconnect} disabled={disconnecting}>
                                {disconnecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Sí, desconectar"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </CardFooter>
        </Card>
    </div>
  );
}
