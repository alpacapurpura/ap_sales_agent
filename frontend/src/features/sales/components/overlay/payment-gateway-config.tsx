"use client";

import { useState } from "react";
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from "@/components/ui/dialog";
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from "@/components/ui/tabs";
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { 
  CreditCard, 
  Key, 
  Lock, 
  CheckCircle2, 
  AlertCircle,
  Loader2,
  ShieldCheck,
  ShieldAlert
} from "lucide-react";
import { PaymentGatewayConfig as ConfigType } from "../../types/sales-studio";

interface PaymentGatewayConfigProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PaymentGatewayConfig({ open, onOpenChange }: PaymentGatewayConfigProps) {
  const [activeProvider, setActiveProvider] = useState<"culqi" | "mercadopago">("culqi");
  const [mode, setMode] = useState<"sandbox" | "production">("sandbox");
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(null);

  // Mock state for keys
  const [config, setConfig] = useState<Record<string, ConfigType>>({
    culqi: {
      provider: "culqi",
      mode: "sandbox",
      sandboxKeys: { publicKey: "", secretKey: "" },
      productionKeys: { publicKey: "", secretKey: "" },
      isEnabled: false
    },
    mercadopago: {
      provider: "mercadopago",
      mode: "sandbox",
      sandboxKeys: { publicKey: "", secretKey: "" },
      productionKeys: { publicKey: "", secretKey: "" },
      isEnabled: false
    }
  });

  const handleModeChange = (checked: boolean) => {
    setMode(checked ? "production" : "sandbox");
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    // Simulate API call
    setTimeout(() => {
      setIsTesting(false);
      // Mock validation logic: success if fields are not empty
      const currentConfig = config[activeProvider];
      const keys = mode === "sandbox" ? currentConfig.sandboxKeys : currentConfig.productionKeys;
      
      if (keys.publicKey && keys.secretKey) {
        setTestResult("success");
      } else {
        setTestResult("error");
      }
    }, 1500);
  };

  const updateKeys = (keyType: "publicKey" | "secretKey", value: string) => {
    setConfig(prev => ({
      ...prev,
      [activeProvider]: {
        ...prev[activeProvider],
        [mode === "sandbox" ? "sandboxKeys" : "productionKeys"]: {
          ...prev[activeProvider][mode === "sandbox" ? "sandboxKeys" : "productionKeys"],
          [keyType]: value
        }
      }
    }));
  };

  const currentConfig = config[activeProvider];
  const currentKeys = mode === "sandbox" ? currentConfig.sandboxKeys : currentConfig.productionKeys;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            Configuración de Pagos
          </DialogTitle>
          <DialogDescription>
            Gestiona tus pasarelas de pago y credenciales de API.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="culqi" value={activeProvider} onValueChange={(v) => setActiveProvider(v as any)} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="culqi">Culqi</TabsTrigger>
            <TabsTrigger value="mercadopago">Mercado Pago</TabsTrigger>
          </TabsList>
          
          <div className="mt-6 space-y-6">
            <div className="flex items-center justify-between p-4 border rounded-lg bg-muted/20">
              <div className="space-y-0.5">
                <Label className="text-base">Entorno de Ejecución</Label>
                <p className="text-sm text-muted-foreground">
                  {mode === "sandbox" ? "Modo Pruebas (No cobra dinero real)" : "Modo Producción (Transacciones reales)"}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium ${mode === "sandbox" ? "text-yellow-600" : "text-muted-foreground"}`}>Sandbox</span>
                <Switch 
                  checked={mode === "production"} 
                  onCheckedChange={handleModeChange}
                />
                <span className={`text-xs font-medium ${mode === "production" ? "text-green-600" : "text-muted-foreground"}`}>Producción</span>
              </div>
            </div>

            <Card className={mode === "sandbox" ? "border-yellow-200 bg-yellow-50/10" : "border-green-200 bg-green-50/10"}>
              <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center justify-between">
                  Credenciales de {activeProvider === "culqi" ? "Culqi" : "Mercado Pago"} ({mode})
                  {mode === "sandbox" ? 
                    <Badge variant="outline" className="border-yellow-500 text-yellow-600 gap-1"><ShieldCheck className="h-3 w-3"/> Test Mode</Badge> : 
                    <Badge variant="outline" className="border-green-500 text-green-600 gap-1"><ShieldAlert className="h-3 w-3"/> Live Mode</Badge>
                  }
                </CardTitle>
                <CardDescription>
                  Ingresa las llaves proporcionadas por tu proveedor de pagos.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="public-key">Public Key / API Key</Label>
                  <div className="relative">
                    <Key className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                      id="public-key" 
                      placeholder={mode === "sandbox" ? "pk_test_..." : "pk_live_..."}
                      className="pl-9" 
                      value={currentKeys.publicKey}
                      onChange={(e) => updateKeys("publicKey", e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secret-key">Secret Key / Access Token</Label>
                  <div className="relative">
                    <Lock className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                      id="secret-key" 
                      type="password"
                      placeholder={mode === "sandbox" ? "sk_test_..." : "sk_live_..."}
                      className="pl-9" 
                      value={currentKeys.secretKey}
                      onChange={(e) => updateKeys("secretKey", e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between border-t px-6 py-4">
                 <div className="flex items-center gap-2">
                   {testResult === "success" && (
                     <span className="flex items-center text-sm text-green-600 font-medium animate-in fade-in">
                       <CheckCircle2 className="mr-1 h-4 w-4" /> Conexión Exitosa
                     </span>
                   )}
                   {testResult === "error" && (
                     <span className="flex items-center text-sm text-destructive font-medium animate-in fade-in">
                       <AlertCircle className="mr-1 h-4 w-4" /> Error de Autenticación
                     </span>
                   )}
                 </div>
                 <Button 
                   variant={testResult === "success" ? "outline" : "secondary"} 
                   onClick={handleTestConnection}
                   disabled={isTesting}
                 >
                   {isTesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                   {isTesting ? "Validando..." : "Probar Conexión"}
                 </Button>
              </CardFooter>
            </Card>
          </div>

          <div className="mt-6 flex justify-end gap-3">
             <Button variant="outline" onClick={() => onOpenChange(false)}>Cancelar</Button>
             <Button onClick={() => onOpenChange(false)}>Guardar Cambios</Button>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
