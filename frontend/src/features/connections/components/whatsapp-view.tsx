"use client";

import { useWhatsApp } from "../hooks/use-whatsapp";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
    Loader2, 
    QrCode, 
    ShieldCheck, 
    AlertTriangle, 
    CheckCircle, 
    Smartphone, 
    ChevronRight,
    Calendar,
    Hash,
    Server,
    LogOut
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
    SheetFooter,
    SheetClose
} from "@/components/ui/sheet";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
  } from "@/components/ui/alert-dialog";

export default function WhatsAppView() {
  const { loading, status, qrCode, isScanning, setIsScanning, generateQR, disconnect } = useWhatsApp();

  if (loading && !status) {
    return (
      <Card>
         <CardContent className="py-10 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
         </CardContent>
      </Card>
    );
  }

  const evoConnected = status?.evolution.status === "connected";
  const metaConnected = status?.meta.status === "connected";
  const anyConnected = evoConnected || metaConnected;
  
  // Helper to format JID to Phone Number
  const formatPhoneNumber = (jid?: string) => {
      if (!jid) return "Desconocido";
      return `+${jid.split("@")[0]}`;
  };

  return (
    <div className="space-y-6">
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Smartphone className="h-6 w-6 text-green-500" />
                        WhatsApp
                    </div>
                    {anyConnected && (
                        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full border border-green-100">
                            <CheckCircle className="h-4 w-4" />
                            Activo
                        </div>
                    )}
                </CardTitle>
                <CardDescription>
                    Conecta tu cuenta de WhatsApp para responder automáticamente. Puedes usar el modo QR (rápido) o la API Oficial (empresas).
                </CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                    
                    {/* --- OPTION 1: EVOLUTION / QR --- */}
                    <Sheet>
                        {/* 
                            Logic: If connected, the whole card is a trigger. 
                            If not connected, we just render the card normally without trigger behavior 
                            (unless we want a sheet for setup too, but requirements say "click opens details").
                        */}
                        {evoConnected ? (
                            <SheetTrigger asChild>
                                <div className={cn(
                                    "relative border rounded-lg p-5 flex flex-col transition-all cursor-pointer group",
                                    "bg-green-50/30 border-green-200 hover:border-green-500/50 hover:shadow-sm"
                                )}>
                                    <div className="flex items-start justify-between mb-4">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-lg bg-green-100 text-green-600">
                                                <QrCode className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-sm group-hover:text-green-700 transition-colors">Modo Sincronizado</h3>
                                                <p className="text-xs text-muted-foreground">Evolution API</p>
                                            </div>
                                        </div>
                                        <Badge variant="outline" className="text-green-600 bg-green-50 border-green-200">
                                            Conectado
                                        </Badge>
                                    </div>
                                    
                                    <div className="mt-auto pt-4 border-t border-green-100 flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <Avatar className="h-6 w-6">
                                                <AvatarImage src={status?.evolution.profile?.profile_pic_url} />
                                                <AvatarFallback className="text-[10px] bg-green-100 text-green-700">
                                                    {status?.evolution.profile?.first_name?.[0] || "W"}
                                                </AvatarFallback>
                                            </Avatar>
                                            <span className="text-xs font-medium text-green-800">
                                                {formatPhoneNumber(status?.evolution.profile?.remote_jid)}
                                            </span>
                                        </div>
                                        <ChevronRight className="h-4 w-4 text-green-400 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            </SheetTrigger>
                        ) : (
                            // Not Connected State - Regular Div
                            <div className="relative border rounded-lg p-5 flex flex-col bg-card hover:border-green-500/50 transition-all">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-green-100 text-green-600">
                                            <QrCode className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-sm">Modo Sincronizado</h3>
                                            <p className="text-xs text-muted-foreground">Escaneo de QR</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex-1">
                                    {isScanning ? (
                                        <div className="flex flex-col items-center justify-center space-y-3">
                                            {qrCode ? (
                                                <div className="relative group">
                                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                                    <img src={qrCode} alt="WhatsApp QR" className="w-32 h-32 border rounded-lg" />
                                                </div>
                                            ) : (
                                                <div className="flex flex-col items-center py-6">
                                                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mb-2" />
                                                    <p className="text-xs text-muted-foreground">Cargando...</p>
                                                </div>
                                            )}
                                            <Button variant="ghost" size="sm" onClick={() => setIsScanning(false)} className="h-7 text-xs">Cancelar</Button>
                                        </div>
                                    ) : (
                                        <div className="space-y-3">
                                            <ul className="space-y-1.5 text-xs text-muted-foreground">
                                                <li className="flex items-center gap-2"><CheckCircle className="h-3 w-3 text-green-500" /> Ideal para Startups</li>
                                                <li className="flex items-center gap-2"><CheckCircle className="h-3 w-3 text-green-500" /> Mantienes tu App Móvil</li>
                                            </ul>
                                            <Button className="w-full" variant="secondary" size="sm" onClick={generateQR}>
                                                Conectar
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* SHEET CONTENT (DETAILS) */}
                        <SheetContent className="sm:max-w-md">
                            <SheetHeader className="pb-6 border-b">
                                <SheetTitle className="flex items-center gap-2">
                                    <div className="p-2 rounded-full bg-green-100 text-green-600">
                                        <Smartphone className="h-5 w-5" />
                                    </div>
                                    Detalles de Conexión
                                </SheetTitle>
                                <SheetDescription>
                                    Información técnica y estado de tu sesión de WhatsApp.
                                </SheetDescription>
                            </SheetHeader>
                            
                            <div className="py-6 space-y-6">
                                {/* Profile Section */}
                                <div className="flex flex-col items-center justify-center space-y-3 pb-6 border-b">
                                    <Avatar className="h-20 w-20 border-4 border-green-50">
                                        <AvatarImage src={status?.evolution.profile?.profile_pic_url} />
                                        <AvatarFallback className="text-xl bg-green-100 text-green-700">
                                            {status?.evolution.profile?.first_name?.[0] || "W"}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="text-center">
                                        <h4 className="text-lg font-semibold text-foreground">
                                            {status?.evolution.profile?.first_name || "WhatsApp User"}
                                        </h4>
                                        <p className="text-sm text-muted-foreground">
                                            {formatPhoneNumber(status?.evolution.profile?.remote_jid)}
                                        </p>
                                    </div>
                                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 px-3 py-1">
                                        ● Sincronizado
                                    </Badge>
                                </div>

                                {/* Metadata Grid */}
                                <div className="grid gap-4">
                                    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                                        <div className="flex items-center gap-3">
                                            <Hash className="h-4 w-4 text-muted-foreground" />
                                            <span className="text-sm font-medium">Plataforma</span>
                                        </div>
                                        <span className="text-sm text-muted-foreground capitalize">
                                            {status?.evolution.profile?.platform || "WhatsApp"}
                                        </span>
                                    </div>
                                    
                                    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                                        <div className="flex items-center gap-3">
                                            <Server className="h-4 w-4 text-muted-foreground" />
                                            <span className="text-sm font-medium">Proveedor</span>
                                        </div>
                                        <span className="text-sm text-muted-foreground">
                                            Evolution API
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                                        <div className="flex items-center gap-3">
                                            <Calendar className="h-4 w-4 text-muted-foreground" />
                                            <span className="text-sm font-medium">Desde</span>
                                        </div>
                                        <span className="text-sm text-muted-foreground">
                                            {status?.evolution.profile?.connected_at || "Reciente"}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <SheetFooter className="pt-6 sm:justify-between sm:space-x-0">
                                <SheetClose asChild>
                                    <Button variant="outline">Cerrar</Button>
                                </SheetClose>
                                
                                <AlertDialog>
                                    <AlertDialogTrigger asChild>
                                        <Button variant="destructive" className="gap-2">
                                            <LogOut className="h-4 w-4" />
                                            Desconectar Sesión
                                        </Button>
                                    </AlertDialogTrigger>
                                    <AlertDialogContent>
                                        <AlertDialogHeader>
                                            <AlertDialogTitle>¿Estás completamente seguro?</AlertDialogTitle>
                                            <AlertDialogDescription>
                                                Esta acción desconectará el agente de tu WhatsApp. Dejará de responder mensajes automáticamente hasta que vuelvas a escanear el código QR.
                                            </AlertDialogDescription>
                                        </AlertDialogHeader>
                                        <AlertDialogFooter>
                                            <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                            <AlertDialogAction 
                                                onClick={() => disconnect("evolution")}
                                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                            >
                                                Sí, desconectar
                                            </AlertDialogAction>
                                        </AlertDialogFooter>
                                    </AlertDialogContent>
                                </AlertDialog>
                            </SheetFooter>
                        </SheetContent>
                    </Sheet>

                    {/* --- OPTION 2: META OFFICIAL --- */}
                    <div className={cn(
                        "relative border rounded-lg p-5 flex flex-col transition-all",
                        metaConnected ? "bg-blue-50/30 border-blue-200" : "bg-card hover:border-blue-500/50"
                    )}>
                        {/* Header */}
                        <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div className={cn("p-2 rounded-lg", metaConnected ? "bg-blue-100 text-blue-600" : "bg-blue-100 text-blue-600")}>
                                    <ShieldCheck className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-sm">API Oficial</h3>
                                    <p className="text-xs text-muted-foreground">Meta Business</p>
                                </div>
                            </div>
                            {metaConnected && <Badge variant="outline" className="text-blue-600 bg-blue-50 border-blue-200">Conectado</Badge>}
                        </div>

                        {/* Content */}
                        <div className="flex-1">
                            {metaConnected ? (
                                <div className="space-y-3">
                                    <div className="flex items-center gap-3 p-3 bg-background rounded border border-blue-100">
                                        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-xs">M</div>
                                        <div>
                                            <p className="font-medium text-sm">Meta Account</p>
                                            <p className="text-xs text-muted-foreground">Cloud API</p>
                                        </div>
                                    </div>
                                    <Button variant="destructive" size="sm" className="w-full h-8 text-xs" onClick={() => disconnect("meta")}>
                                        Desconectar
                                    </Button>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <ul className="space-y-1.5 text-xs text-muted-foreground">
                                        <li className="flex items-center gap-2"><CheckCircle className="h-3 w-3 text-blue-500" /> Alta Estabilidad</li>
                                        <li className="flex items-center gap-2"><AlertTriangle className="h-3 w-3 text-amber-500" /> Requiere Verificación</li>
                                    </ul>
                                    <Button className="w-full" variant="outline" size="sm" disabled>
                                        Próximamente
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>

                </div>
            </CardContent>
            
            <CardFooter className="border-t pt-6">
                <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 p-3 rounded w-full">
                    <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                    <p>Nota: Puedes tener ambas conexiones configuradas, pero te recomendamos usar solo una activa para evitar respuestas duplicadas.</p>
                </div>
            </CardFooter>
        </Card>
    </div>
  );
}
