"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi, MailerliteStatusResponse } from "@/lib/api/connections";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

export function MailerLiteView() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<MailerliteStatusResponse | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getMailerLiteStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de MailerLite");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleConnect = async () => {
    if (!apiKey.trim()) {
        toast.error("Por favor ingresa la API Key");
        return;
    }

    try {
        setConnecting(true);
        const token = await getToken();
        if (!token) return;

        await connectionsApi.connectMailerLite({ api_key: apiKey }, token);
        toast.success("MailerLite conectado exitosamente");
        fetchStatus();
        setApiKey("");
    } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Error al conectar MailerLite");
    } finally {
        setConnecting(false);
    }
  };

  const handleTest = async () => {
      try {
          setTesting(true);
          setTestResult(null);
          const token = await getToken();
          if (!token) return;
          
          const res = await connectionsApi.testMailerLite(token);
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

          await connectionsApi.disconnectMailerLite(token);
          toast.success("MailerLite desconectado");
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
      // STATE 1: NOT CONNECTED
      return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Mail className="h-6 w-6 text-green-600" />
                    Conectar con MailerLite
                </CardTitle>
                <CardDescription>
                    Vincula tu cuenta de MailerLite para sincronizar contactos y campañas.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-4 border rounded-md p-4 bg-muted/20">
                    <h3 className="font-medium text-sm">Instrucciones:</h3>
                    <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-2">
                        <li>Inicia sesión en tu cuenta de MailerLite.</li>
                        <li>Navega a <strong>Integrations {'>'} API</strong>.</li>
                        <li>Haz clic en <strong>Generate new token</strong>.</li>
                        <li>Dale un nombre al token y copia la clave generada.</li>
                        <li>Pega la clave en el campo de abajo.</li>
                    </ol>
                </div>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="apiKey">API Key</Label>
                        <Input 
                            id="apiKey" 
                            placeholder="Introduce tu API Key aquí..." 
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            type="password"
                        />
                    </div>
                </div>
            </CardContent>
            <CardFooter>
                <Button onClick={handleConnect} disabled={connecting} className="w-full sm:w-auto">
                    {connecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Mail className="mr-2 h-4 w-4" />}
                    Conectar MailerLite
                </Button>
            </CardFooter>
        </Card>
      );
  }

  // STATE 2: CONNECTED
  return (
    <div className="space-y-6">
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Mail className="h-6 w-6 text-green-600" />
                        MailerLite Conectado
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                        <CheckCircle className="h-4 w-4" />
                        Activo
                    </div>
                </CardTitle>
                <CardDescription>
                    Tu agente está sincronizado con esta cuenta de MailerLite.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-1">
                        <Label className="text-muted-foreground text-xs uppercase tracking-wider">Cuenta</Label>
                        <p className="font-medium text-lg flex items-center gap-2">
                            {status.account_info?.data?.name || "Desconocido"}
                        </p>
                    </div>
                    <div className="space-y-1">
                        <Label className="text-muted-foreground text-xs uppercase tracking-wider">Email</Label>
                        <p className="font-medium text-sm text-muted-foreground break-all">
                            {status.account_info?.data?.email || "N/A"}
                        </p>
                    </div>
                </div>

                {testResult && (
                    <Alert variant={testResult.status === "active" ? "default" : "destructive"} className={testResult.status === "active" ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20" : ""}>
                        <Activity className="h-4 w-4" />
                        <AlertTitle>{testResult.status === "active" ? "Conexión Estable" : "Error de Conexión"}</AlertTitle>
                        <AlertDescription>
                            {testResult.message}
                            {testResult.details && (
                                <pre className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50">
                                    {JSON.stringify(testResult.details, null, 2)}
                                </pre>
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
                            <DialogTitle>¿Estás seguro?</DialogTitle>
                            <DialogDescription>
                                Esto eliminará la conexión con MailerLite. El agente dejará de sincronizar datos inmediatamente.
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
