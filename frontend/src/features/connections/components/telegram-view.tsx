"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi, ChannelStatusResponse } from "@/lib/api/connections";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, CheckCircle, AlertTriangle, Send, Trash2, ExternalLink, Activity } from "lucide-react";
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

export function TelegramView() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<ChannelStatusResponse | null>(null);
  const [tokenInput, setTokenInput] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getTelegramStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Telegram");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleConnect = async () => {
    if (!tokenInput.trim()) {
        toast.error("Por favor ingresa el Token");
        return;
    }

    try {
        setConnecting(true);
        const token = await getToken();
        if (!token) return;

        await connectionsApi.connectTelegram({ token: tokenInput }, token);
        toast.success("Telegram conectado exitosamente");
        fetchStatus();
        setTokenInput("");
    } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Error al conectar Telegram");
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
          
          const res = await connectionsApi.testTelegram(token);
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

          await connectionsApi.disconnectTelegram(token);
          toast.success("Telegram desconectado");
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
                    <Send className="h-6 w-6 text-blue-500" />
                    Conectar con Telegram
                </CardTitle>
                <CardDescription>
                    Vincula un Bot de Telegram para que tu Agente pueda responder mensajes automáticamente.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-4 border rounded-md p-4 bg-muted/20">
                    <h3 className="font-medium text-sm">Instrucciones para obtener el Token:</h3>
                    <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-2">
                        <li>Abre Telegram y busca el usuario <strong>@BotFather</strong>.</li>
                        <li>Envía el comando <code>/newbot</code> para crear un nuevo bot.</li>
                        <li>Sigue las instrucciones para asignarle un nombre y un usuario.</li>
                        <li>BotFather te entregará un <strong>API Token</strong> (ej. <code>123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11</code>).</li>
                        <li>Copia ese token y pégalo abajo.</li>
                    </ol>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="token">Telegram Bot Token</Label>
                    <Input 
                        id="token" 
                        placeholder="123456:ABC-DEF..." 
                        value={tokenInput}
                        onChange={(e) => setTokenInput(e.target.value)}
                        type="password"
                    />
                </div>
            </CardContent>
            <CardFooter>
                <Button onClick={handleConnect} disabled={connecting} className="w-full sm:w-auto">
                    {connecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                    Conectar Bot
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
                        <Send className="h-6 w-6 text-blue-500" />
                        Telegram Conectado
                    </div>
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                        <CheckCircle className="h-4 w-4" />
                        Activo
                    </div>
                </CardTitle>
                <CardDescription>
                    Tu agente está escuchando mensajes en este canal.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-1">
                        <Label className="text-muted-foreground text-xs uppercase tracking-wider">Nombre del Bot</Label>
                        <p className="font-medium text-lg">{status.bot_name || "Desconocido"}</p>
                    </div>
                    <div className="space-y-1">
                        <Label className="text-muted-foreground text-xs uppercase tracking-wider">Usuario</Label>
                        <p className="font-medium text-lg flex items-center gap-2">
                            @{status.username || "..."}
                            {status.username && (
                                <a href={`https://t.me/${status.username}`} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">
                                    <ExternalLink className="h-4 w-4" />
                                </a>
                            )}
                        </p>
                    </div>
                </div>

                {testResult && (
                    <Alert variant={testResult.status === "ok" ? "default" : "destructive"} className={testResult.status === "ok" ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20" : ""}>
                        <Activity className="h-4 w-4" />
                        <AlertTitle>{testResult.status === "ok" ? "Conexión Estable" : "Error de Conexión"}</AlertTitle>
                        <AlertDescription>
                            {testResult.message}
                            {testResult.data && (
                                <pre className="mt-2 text-xs bg-background/50 p-2 rounded overflow-x-auto text-foreground border border-border/50">
                                    {JSON.stringify(testResult.data, null, 2)}
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
                                Esto eliminará la conexión con el bot. El agente dejará de responder mensajes de Telegram inmediatamente.
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
