"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useSearchParams, useRouter } from "next/navigation";
import { connectionsApi } from "@/lib/api/connections";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, CheckCircle, Mail, Trash2, ExternalLink, Activity } from "lucide-react";
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

export function GmailView() {
  const { getToken } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<{ is_connected: boolean; email?: string } | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getGmailStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Gmail");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle OAuth Callback (Popup Listener)
  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      
      if (event.data?.type === "GOOGLE_OAUTH_SUCCESS" && event.data?.code) {
         try {
          setConnecting(true);
          const token = await getToken();
          if (!token) return;

          toast.info("Finalizando conexión con Gmail...");
          
          // Use the callback route as redirect URI
          const redirectUri = window.location.origin + "/connections";
          
          await connectionsApi.connectGmail(event.data.code, token, redirectUri);
          toast.success("Gmail conectado exitosamente");
          
          await fetchStatus();
        } catch (error: any) {
          console.error(error);
          toast.error(error.message || "Error al conectar Gmail");
        } finally {
          setConnecting(false);
        }
      } else if (event.data?.type === "GOOGLE_OAUTH_ERROR") {
          toast.error("Error en autenticación de Google");
          setConnecting(false);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;

      // Use the dedicated callback route
      const redirectUri = window.location.origin + "/connections";
      const { url } = await connectionsApi.getGmailAuthUrl(token, redirectUri);
      
      // Open Popup
      const width = 500;
      const height = 600;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      
      window.open(
        url,
        "GoogleAuth",
        `width=${width},height=${height},top=${top},left=${left},toolbar=no,menubar=no,scrollbars=yes,resizable=yes,location=no,status=no`
      );

      setTimeout(() => setConnecting(false), 60000); // 1 min timeout

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
          
          const res = await connectionsApi.testGmail(token);
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

      await connectionsApi.disconnectGmail(token);
      toast.success("Gmail desconectado");
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

  if (!status?.is_connected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-6 w-6 text-red-500" />
            Conectar Correo Electrónico
          </CardTitle>
          <CardDescription>
            Vincula tu cuenta de Gmail para enviar confirmaciones de reserva automáticamente.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
            <Alert className="bg-blue-50 text-blue-800 border-blue-200">
                <ExternalLink className="h-4 w-4" />
                <AlertTitle>Requisito Google Workspace</AlertTitle>
                <AlertDescription>
                    Actualmente solo soportamos cuentas de Google Workspace (Empresariales).
                </AlertDescription>
            </Alert>
            <div className="text-sm text-muted-foreground">
                <p>Al conectar, permitirás que el sistema:</p>
                <ul className="list-disc list-inside mt-2 space-y-1 ml-2">
                    <li>Enviar correos electrónicos en tu nombre.</li>
                    <li>Leer tu dirección de correo para identificación.</li>
                </ul>
            </div>
        </CardContent>
        <CardFooter>
            <Button onClick={handleConnect} disabled={connecting} className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700">
                {connecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Mail className="mr-2 h-4 w-4" />}
                Conectar con Gmail
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
                        <Mail className="h-6 w-6 text-red-500" />
                        Gmail Conectado
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                        <CheckCircle className="h-4 w-4" />
                        Activo
                    </div>
                </CardTitle>
                <CardDescription>
                    Tu correo está conectado y listo para enviar notificaciones.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-1">
                    <span className="text-muted-foreground text-xs uppercase tracking-wider">Cuenta Conectada</span>
                    <p className="font-medium text-lg flex items-center gap-2">
                        {status.email || "Usuario de Google"}
                        {status.email && (
                            <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground font-normal">
                                {status.email.split('@')[1]}
                            </span>
                        )}
                    </p>
                </div>

                {testResult && (
                    <Alert variant={testResult.status === "ok" ? "default" : "destructive"} className={testResult.status === "ok" ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20" : ""}>
                        <Activity className="h-4 w-4" />
                        <AlertTitle>{testResult.status === "ok" ? "Conexión Estable" : "Error de Conexión"}</AlertTitle>
                        <AlertDescription>
                            {testResult.message}
                            {testResult.data && (
                                <div className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50 grid gap-1">
                                    <div><strong>Email:</strong> {testResult.data.emailAddress}</div>
                                    <div><strong>Mensajes Total:</strong> {testResult.data.messagesTotal}</div>
                                    <div><strong>Threads Total:</strong> {testResult.data.threadsTotal}</div>
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
                            <DialogTitle>¿Desvincular Gmail?</DialogTitle>
                            <DialogDescription>
                                El sistema dejará de enviar correos de confirmación automáticamente.
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
