"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, CheckCircle, ShoppingBag, Trash2, ExternalLink, Activity } from "lucide-react";
import { useSearchParams, useRouter, useParams } from "next/navigation";
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

import type { ShopifyStatusResponse, TestResponse } from "@/lib/api/connections";

/**
 *
 */
export function ShopifyView() {
  const { getToken } = useAuth();
  const searchParams = useSearchParams();
  const router = useRouter();
  const params = useParams();
  const tenantId = params?.tenantId as string | undefined;
  const externalStudioBaseUrl = (process.env.NEXT_PUBLIC_APP_URL || "").replace(/\/$/, "");
  const nicolifyStudioUrl = `${externalStudioBaseUrl}/growth-studio`;
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<ShopifyStatusResponse | null>(null);
  const [shopUrl, setShopUrl] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [testResult, setTestResult] = useState<TestResponse | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await connectionsApi.getShopifyStatus(token);
      setStatus(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar estado de Shopify");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    const statusParam = searchParams?.get("status");
    const channel = searchParams?.get("channel");
    const message = searchParams?.get("message");
    if (statusParam === "success" && channel === "shopify") {
      toast.success("Shopify conectado exitosamente");
      router.replace(tenantId ? `/${tenantId}/connections/shopify` : "/");
      void fetchStatus();
    }
    if (statusParam === "error" && message) {
      toast.error(message);
      router.replace(tenantId ? `/${tenantId}/connections/shopify` : "/");
    }
  }, [searchParams, router, tenantId, fetchStatus]);

  const handleConnect = async () => {
    if (!shopUrl.trim()) {
      toast.error("Por favor ingresa la URL de la tienda");
      return;
    }

    // Clean shop URL: remove https://, http://, slashes
    let cleanShopUrl = shopUrl.replace("https://", "").replace("http://", "").split("/")[0];

    // Validate domain format
    if (!cleanShopUrl.includes(".")) {
      cleanShopUrl = `${cleanShopUrl}.myshopify.com`;
    }

    try {
      setConnecting(true);
      const token = await getToken();
      if (!token) return;

      // Use quick-connect (client credentials) — works for own stores
      await connectionsApi.quickConnectShopify({ shop_url: cleanShopUrl }, token);
      toast.success("Shopify conectado exitosamente");
      void fetchStatus();
    } catch (error: unknown) {
      console.error(error);
      // Fallback: try OAuth redirect if quick-connect fails
      try {
        const token = await getToken();
        if (!token) return;
        const authRes = await connectionsApi.generateShopifyAuthUrl(
          { shop_url: cleanShopUrl },
          token,
        );
        if (authRes.auth_url) {
          window.location.href = authRes.auth_url;
          return;
        }
      } catch (fallbackError: unknown) {
        console.error("OAuth fallback also failed:", fallbackError);
      }
      toast.error(error instanceof Error ? error.message : "Error al conectar con Shopify");
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

      const res = await connectionsApi.testShopify(token);
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

      await connectionsApi.disconnectShopify(token);
      toast.success("Shopify desconectado");
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
    // STATE 1: NOT CONNECTED
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShoppingBag className="h-6 w-6 text-green-600" />
            Conectar con Shopify
          </CardTitle>
          <CardDescription>
            Vincula tu tienda de Shopify para sincronizar productos y órdenes.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4 border rounded-md p-4 bg-muted/20">
            <h3 className="font-medium text-sm">Instrucciones:</h3>
            <ol className="list-decimal list-inside text-sm text-muted-foreground space-y-2">
              <li>Ingresa la URL de tu tienda Shopify (ej: mi-tienda.myshopify.com).</li>
              <li>Haz clic en Conectar Tienda para ser redirigido a Shopify.</li>
              <li>Aprueba la instalación de la aplicación en tu panel de Shopify.</li>
            </ol>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="shopUrl">URL de la tienda (ej: mi-tienda.myshopify.com)</Label>
              <Input
                id="shopUrl"
                placeholder="mi-tienda.myshopify.com"
                value={shopUrl}
                onChange={(e) => setShopUrl(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleConnect} disabled={connecting} className="w-full sm:w-auto">
            {connecting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <ShoppingBag className="mr-2 h-4 w-4" />
            )}
            Conectar con Shopify
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
              <ShoppingBag className="h-6 w-6 text-green-600" />
              Shopify Conectado
            </div>
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
              <CheckCircle className="h-4 w-4" />
              Activo
            </div>
          </CardTitle>
          <CardDescription>Tu agente está sincronizado con esta tienda de Shopify.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <Label className="text-muted-foreground text-xs uppercase tracking-wider">
                URL de la Tienda
              </Label>
              <p className="font-medium text-lg flex items-center gap-2">
                {status.shop_url || "Desconocido"}
                {status.shop_url && (
                  <a
                    href={`https://${status.shop_url}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-500 hover:underline"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </p>
            </div>
            <div className="space-y-1">
              <Label className="text-muted-foreground text-xs uppercase tracking-wider">
                Scope
              </Label>
              <p className="font-medium text-sm text-muted-foreground break-all">
                {status.scope || "N/A"}
              </p>
            </div>
          </div>

          {testResult && (
            <Alert
              variant={
                testResult.status === "ok" || testResult.status === "active"
                  ? "default"
                  : "destructive"
              }
              className={
                testResult.status === "ok" || testResult.status === "active"
                  ? "bg-green-500/15 text-green-700 border-green-500/30 dark:bg-green-500/10 dark:text-green-400 dark:border-green-500/20"
                  : ""
              }
            >
              <Activity className="h-4 w-4" />
              <AlertTitle>
                {testResult.status === "ok" || testResult.status === "active"
                  ? "Conexión Estable"
                  : "Error de Conexión"}
              </AlertTitle>
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
            {testing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Activity className="mr-2 h-4 w-4" />
            )}
            Probar Conexión
          </Button>
          <Button asChild variant="secondary">
            <a href={nicolifyStudioUrl} target="_blank" rel="noreferrer">
              <ExternalLink className="mr-2 h-4 w-4" />
              Abrir Nicolify Studio
            </a>
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
                  Esto eliminará la conexión con Shopify. El agente dejará de sincronizar datos
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
