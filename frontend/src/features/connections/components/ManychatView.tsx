"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, CheckCircle, MessageCircle, Trash2, Activity } from "lucide-react";
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
import { connectionsApi } from "@/lib/api/connections";

import type { ManyChatStatusResponse, TestResponse } from "@/lib/api/connections";

export function ManyChatView() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<ManyChatStatusResponse | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testResult, setTestResult] = useState<TestResponse | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getManyChatStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de ManyChat");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  const handleConnect = async () => {
    if (!apiKey.trim()) {
      toast.error("Por favor ingresa la API Key");
      return;
    }

    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;

      await connectionsApi.connectManyChat({ api_key: apiKey }, token);
      toast.success("ManyChat conectado exitosamente");
      void fetchStatus();
      setApiKey("");
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Error al conectar ManyChat";
      console.error(error);
      toast.error(message);
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

      const res = await connectionsApi.testManyChat(token);
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

      await connectionsApi.disconnectManyChat(token);
      toast.success("ManyChat desconectado");
      setStatus({ is_connected: false });
      setTestResult(null);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Error al desconectar";
      console.error(error);
      toast.error(message);
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
            <MessageCircle className="h-6 w-6 text-blue-600" />
            Conectar con ManyChat
          </CardTitle>
          <CardDescription>
            Vincula tu cuenta de ManyChat para automatizar conversaciones.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4 border rounded-md p-4 bg-muted/20">
            <h3 className="font-medium text-sm">Instrucciones:</h3>
            <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-2">
              <li>Inicia sesión en tu cuenta de ManyChat.</li>
              <li>
                Ve a <strong>Settings {">"} API</strong>.
              </li>
              <li>Genera un nuevo Token.</li>
              <li>Copia el Token y pégalo en el campo de abajo.</li>
            </ol>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="apiKey">API Token</Label>
              <Input
                id="apiKey"
                placeholder="Introduce tu API Token aquí..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                type="password"
              />
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleConnect} disabled={connecting} className="w-full sm:w-auto">
            {connecting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <MessageCircle className="mr-2 h-4 w-4" />
            )}
            Conectar ManyChat
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
              <MessageCircle className="h-6 w-6 text-blue-600" />
              ManyChat Conectado
            </div>
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
              <CheckCircle className="h-4 w-4" />
              Activo
            </div>
          </CardTitle>
          <CardDescription>
            Tu agente está sincronizado con esta cuenta de ManyChat.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <Label className="text-muted-foreground text-xs uppercase tracking-wider">
                Página / Cuenta
              </Label>
              <p className="font-medium text-lg flex items-center gap-2">
                {(status.account_info?.name as string) || "Desconocido"}
              </p>
            </div>
            <div className="space-y-1">
              <Label className="text-muted-foreground text-xs uppercase tracking-wider">ID</Label>
              <p className="font-medium text-sm text-muted-foreground break-all">
                {(status.account_info?.id as string) || "N/A"}
              </p>
            </div>
          </div>

          {testResult && (
            <Alert
              variant={testResult.status === "active" ? "default" : "destructive"}
              className={
                testResult.status === "active"
                  ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20"
                  : ""
              }
            >
              <Activity className="h-4 w-4" />
              <AlertTitle>
                {testResult.status === "active" ? "Conexión Estable" : "Error de Conexión"}
              </AlertTitle>
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
                <DialogTitle>¿Estás seguro?</DialogTitle>
                <DialogDescription>
                  Esto eliminará la conexión con ManyChat. El agente dejará de sincronizar datos
                  inmediatamente.
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
