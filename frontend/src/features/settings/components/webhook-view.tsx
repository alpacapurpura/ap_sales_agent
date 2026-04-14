"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { settingsApi, WebhookSettings } from "@/lib/api/settings";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, Copy, RefreshCw, Eye, EyeOff, AlertTriangle, CheckCircle } from "lucide-react";
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

export function WebhookView() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [settings, setSettings] = useState<WebhookSettings | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      const data = await settingsApi.getWebhookSettings(token);
      setSettings(data);
    } catch (error) {
      console.error(error);
      toast.error("Error al cargar configuración de Webhook");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copiado al portapapeles`);
  };

  const handleRegenerate = async () => {
    try {
      setRegenerating(true);
      const token = await getToken();
      if (!token) return;

      const data = await settingsApi.regenerateWebhookSecret(token);
      setSettings(data);
      toast.success("Secret Key regenerado exitosamente");
      setConfirmOpen(false);
    } catch (error) {
      console.error(error);
      toast.error("Error al regenerar Secret Key");
    } finally {
      setRegenerating(false);
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Integración Externa (Webhook)</CardTitle>
          <CardDescription>
            Conecta tu Agente IA con plataformas externas como n8n, Make, Flowise o ManyChat.
            Utiliza estos credenciales para enviar mensajes y recibir respuestas del
            &quot;Cerebro&quot;.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Webhook URL */}
          <div className="space-y-2">
            <Label htmlFor="webhook-url">Endpoint URL</Label>
            <div className="flex space-x-2">
              <Input
                id="webhook-url"
                value={settings?.webhook_url || ""}
                readOnly
                className="font-mono text-sm bg-muted/50"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => handleCopy(settings?.webhook_url || "", "URL")}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Realiza peticiones POST a esta URL con el payload JSON adecuado.
            </p>
          </div>

          {/* Secret Key */}
          <div className="space-y-2">
            <Label htmlFor="webhook-secret">Secret Key (X-Webhook-Secret)</Label>
            <div className="flex space-x-2">
              <div className="relative flex-1">
                <Input
                  id="webhook-secret"
                  type={showSecret ? "text" : "password"}
                  value={settings?.webhook_secret || "No generado"}
                  readOnly
                  className="font-mono text-sm bg-muted/50 pr-10"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowSecret(!showSecret)}
                >
                  {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <Button
                variant="outline"
                size="icon"
                disabled={!settings?.webhook_secret}
                onClick={() => handleCopy(settings?.webhook_secret || "", "Secret Key")}
              >
                <Copy className="h-4 w-4" />
              </Button>

              <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="icon"
                    className="text-destructive hover:text-destructive"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>¿Regenerar Secret Key?</DialogTitle>
                    <DialogDescription>
                      Esta acción invalidará la clave actual inmediatamente. Cualquier integración
                      activa (n8n, ManyChat) dejará de funcionar hasta que actualices la clave.
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setConfirmOpen(false)}>
                      Cancelar
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleRegenerate}
                      disabled={regenerating}
                    >
                      {regenerating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                      Regenerar Clave
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
            <p className="text-xs text-muted-foreground">
              Esta clave debe enviarse en el Header <code>X-Webhook-Secret</code>. Nunca la
              compartas públicamente.
            </p>
          </div>

          {!settings?.webhook_secret && (
            <Alert variant="destructive" className="bg-white">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Acceso Desactivado</AlertTitle>
              <AlertDescription>
                Aún no tienes un Secret Key generado. Haz clic en el botón de regenerar para activar
                el acceso externo.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Tabs defaultValue="curl" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="curl">cURL / Postman</TabsTrigger>
          <TabsTrigger value="n8n">n8n / Flowise</TabsTrigger>
          <TabsTrigger value="manychat">ManyChat</TabsTrigger>
        </TabsList>

        <TabsContent value="curl">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Ejemplo de Petición</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto">
                {`curl -X POST "${settings?.webhook_url || "..."}" \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Secret: ${settings?.webhook_secret || "YOUR_SECRET_KEY"}" \\
  -d '{
    "user_id": "usuario_prueba_1",
    "message": "Hola, quiero información sobre el programa",
    "metadata": {
      "first_name": "Juan",
      "source": "api_test"
    }
  }'`}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="n8n">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Configuración HTTP Request Node</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <span className="font-semibold">Method:</span>
                  <div className="bg-muted p-2 rounded">POST</div>
                </div>
                <div className="space-y-1">
                  <span className="font-semibold">Authentication:</span>
                  <div className="bg-muted p-2 rounded">None (Use Headers)</div>
                </div>
              </div>
              <div className="space-y-1">
                <span className="font-semibold">Headers:</span>
                <div className="bg-muted p-2 rounded">
                  <code>X-Webhook-Secret</code> : <code>{settings?.webhook_secret || "..."}</code>
                </div>
              </div>
              <div className="space-y-1">
                <span className="font-semibold">Body Parameters (JSON):</span>
                <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto">
                  {`{
  "user_id": "{{ $json.userId }}",
  "message": "{{ $json.message }}",
  "metadata": {
     "name": "{{ $json.name }}"
  }
}`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="manychat">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">External Request en ManyChat</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <p>
                Usa la acción <strong>External Request</strong> en tu flujo:
              </p>
              <ul className="list-disc pl-5 space-y-2">
                <li>
                  <strong>Request Type:</strong> POST
                </li>
                <li>
                  <strong>Request URL:</strong> Copia la URL de arriba.
                </li>
                <li>
                  <strong>Headers:</strong> Agrega <code>X-Webhook-Secret</code> con tu clave.
                </li>
                <li>
                  <strong>Body:</strong>
                  <pre className="bg-slate-950 text-slate-50 p-4 rounded-lg text-xs overflow-x-auto">
                    {`{
  "user_id": "{{ user_id }}",
  "message": "{{ last_input_text }}",
  "metadata": {
    "first_name": "{{ first_name }}",
    "phone": "{{ phone }}"
  }
}`}
                  </pre>
                </li>
                <li>
                  <strong>Response Mapping:</strong> Mapea <code>$.response</code> a un Custom Field
                  (ej. <code>bot_response</code>).
                </li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
