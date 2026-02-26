"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, PenTool, Rocket, ArrowRight } from "lucide-react";

interface BrandEmptyStateProps {
  onStartAI: () => void;
  onStartManual: () => void;
}

export function BrandEmptyState({ onStartAI, onStartManual }: BrandEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 animate-in fade-in zoom-in duration-500">
      <div className="mb-8 relative">
        <div className="absolute inset-0 bg-primary/20 blur-3xl rounded-full" />
        <div className="relative bg-background p-6 rounded-full shadow-xl border-2 border-primary/10">
            <Rocket className="w-16 h-16 text-primary" />
        </div>
      </div>

      <h1 className="text-4xl font-bold tracking-tight mb-4 max-w-2xl">
        Define el ADN de tu Marca
      </h1>
      <p className="text-xl text-muted-foreground mb-12 max-w-xl mx-auto">
        Comienza configurando tu identidad para generar contenido alineado con tus valores y estilo.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-3xl">
        {/* Option 1: AI (Magic) */}
        <Card 
            className="group relative overflow-hidden border-primary/20 hover:border-primary transition-all cursor-pointer hover:shadow-lg hover:-translate-y-1"
            onClick={onStartAI}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <CardContent className="p-8 flex flex-col items-center text-center h-full justify-between">
                <div className="mb-6 p-4 bg-primary/10 rounded-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <Sparkles className="w-8 h-8" />
                </div>
                <div>
                    <h3 className="text-xl font-bold mb-2">Llenado Inteligente</h3>
                    <p className="text-muted-foreground mb-6">
                        Analizamos tu sitio web o documentos para extraer colores, logos y textos automáticamente.
                    </p>
                </div>
                <Button className="w-full" size="lg">
                    Autocompletar con IA <Sparkles className="ml-2 w-4 h-4" />
                </Button>
            </CardContent>
        </Card>

        {/* Option 2: Manual */}
        <Card 
            className="group relative overflow-hidden hover:border-primary transition-all cursor-pointer hover:shadow-lg hover:-translate-y-1"
            onClick={onStartManual}
        >
            <CardContent className="p-8 flex flex-col items-center text-center h-full justify-between">
                <div className="mb-6 p-4 bg-secondary rounded-full group-hover:bg-secondary/80 transition-colors">
                    <PenTool className="w-8 h-8 text-foreground" />
                </div>
                <div>
                    <h3 className="text-xl font-bold mb-2">Configuración Manual</h3>
                    <p className="text-muted-foreground mb-6">
                        Define cada detalle paso a paso. Ideal si estás construyendo tu marca desde cero.
                    </p>
                </div>
                <Button variant="outline" className="w-full" size="lg">
                    Configurar Manualmente <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
            </CardContent>
        </Card>
      </div>
    </div>
  );
}
