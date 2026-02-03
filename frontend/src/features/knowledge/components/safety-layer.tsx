"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Badge } from "@/components/ui/badge"
import { Building2, Package, Info, Plus, Trash2, CheckCircle2 } from "lucide-react"

export function SafetyLayerManager() {
  const [scope, setScope] = useState<"BRAND" | "PRODUCT">("BRAND")
  
  return (
    <div className="grid gap-6">
      {/* --- HEADER & SCOPE SELECTOR --- */}
      <Card>
        <CardHeader>
          <CardTitle>Ámbito de Protección</CardTitle>
          <CardDescription>
            Define si las reglas de censura aplican a toda la marca o a un producto específico.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup 
            defaultValue="BRAND" 
            onValueChange={(val) => setScope(val as "BRAND" | "PRODUCT")}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {/* BRAND OPTION */}
            <div>
              <RadioGroupItem value="BRAND" id="scope-brand" className="peer sr-only" />
              <Label
                htmlFor="scope-brand"
                className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
              >
                <Building2 className="mb-3 h-6 w-6" />
                <div className="text-center">
                  <div className="font-semibold text-lg">Nivel Marca (Global)</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Aplica a todas las conversaciones y productos.
                  </div>
                </div>
              </Label>
            </div>

            {/* PRODUCT OPTION */}
            <div>
              <RadioGroupItem value="PRODUCT" id="scope-product" className="peer sr-only" />
              <Label
                htmlFor="scope-product"
                className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
              >
                <Package className="mb-3 h-6 w-6" />
                <div className="text-center">
                  <div className="font-semibold text-lg">Nivel Producto</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Aplica solo cuando se habla de un producto específico.
                  </div>
                </div>
              </Label>
            </div>
          </RadioGroup>

          {/* PRODUCT SELECTOR (Conditional) */}
          {scope === "PRODUCT" && (
            <div className="mt-6 animate-in fade-in slide-in-from-top-2">
              <Label>Selecciona el Producto Activo</Label>
              <Select>
                <SelectTrigger className="w-full md:w-[400px] mt-2">
                  <SelectValue placeholder="Ej: Seguro de Vida Premium" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="prod_1">Seguro de Vida Premium</SelectItem>
                  <SelectItem value="prod_2">Asistencia Vehicular 24/7</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </CardContent>
      </Card>

      {/* --- CREATE RULE FORM --- */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5 text-primary" />
            Nueva Regla de Censura
          </CardTitle>
          <CardDescription>
            Configura qué datos deben ser ocultados automáticamente.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* PATTERN */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                Patrón o Palabra Clave
                <Info className="h-3 w-3 text-muted-foreground" />
              </Label>
              <Input placeholder="Ej: \d{4}-\d{4} o CLAVE_SECRETA" />
              <p className="text-[0.8rem] text-muted-foreground">
                Usa palabras exactas o expresiones regulares (Regex).
              </p>
            </div>

            {/* CATEGORY */}
            <div className="space-y-2">
              <Label>Tipo de Dato</Label>
              <Select defaultValue="financial">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="financial">💰 Financiero (Precios, Márgenes)</SelectItem>
                  <SelectItem value="pii">👤 Datos Personales (PII)</SelectItem>
                  <SelectItem value="business_secret">🔒 Secreto Comercial</SelectItem>
                  <SelectItem value="system">🤖 Instrucción de Sistema</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* REPLACEMENT */}
            <div className="space-y-2">
              <Label>Texto de Reemplazo</Label>
              <Input defaultValue="[DATO PROTEGIDO]" />
              <p className="text-[0.8rem] text-muted-foreground">
                Esto es lo que verá el usuario final.
              </p>
            </div>

            {/* DESCRIPTION */}
            <div className="space-y-2">
              <Label>Nota Interna (Opcional)</Label>
              <Input placeholder="Ej: Ocultar margen para evitar regateo" />
            </div>
          </div>

          {/* CONTEXT INSTRUCTION */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <span className="text-primary font-medium">✨ Verificación con IA (Contexto)</span>
            </Label>
            <Textarea 
              placeholder="Ej: Solo censurar si el usuario NO es un administrador, o si se refiere a la clave maestra..." 
              className="h-24 resize-none"
            />
            <p className="text-[0.8rem] text-muted-foreground">
              Si escribes aquí, un modelo de IA verificará el contexto antes de censurar para evitar falsos positivos.
            </p>
          </div>

          <div className="flex justify-end">
            <Button size="lg">Guardar Regla</Button>
          </div>
        </CardContent>
      </Card>

      {/* --- RULES LIST --- */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          📋 Reglas Activas
          <Badge variant="outline" className="text-xs font-normal">
            {scope === "BRAND" ? "Global" : "Producto"}
          </Badge>
        </h3>
        
        {/* Empty State / Example Item */}
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">\d{4}-\d{4}</code>
                <span className="text-muted-foreground">➝</span>
                <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">[TARJETA OCULTA]</code>
                <Badge variant="secondary" className="text-xs">PII</Badge>
              </div>
              <p className="text-sm text-muted-foreground">Ocultar patrones de tarjeta de crédito</p>
            </div>
            <div className="flex items-center gap-2">
              <Switch defaultChecked />
              <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
