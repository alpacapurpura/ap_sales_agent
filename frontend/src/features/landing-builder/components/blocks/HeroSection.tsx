import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useLandingTheme } from '@/features/landing-builder/context/LandingThemeContext';

export interface HeroSectionProps {
    headline: string;
    subheadline: string;
    cta_text: string;
    scarcity_text?: string;
    layout?: "centered" | "split" | "background" | "vsl" | "urgency" | "quiz";
    image_url?: string;
    video_url?: string;
}

export function HeroSection({ 
    headline, 
    subheadline, 
    cta_text, 
    scarcity_text, 
    layout = "centered", 
    image_url,
    video_url
}: HeroSectionProps) {
    const theme = useLandingTheme();
    const primaryColor = theme.primary_color || '#3b82f6';
    
    // Default placeholder if no image provided for split/background
    const bgImage = image_url || "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1574&q=80";

    // 1. VSL Layout (Video Sales Letter)
    if (layout === "vsl") {
        return (
            <section className="relative py-16 px-6 text-center bg-white border-b border-slate-100">
                <div className="max-w-4xl mx-auto space-y-8">
                    {/* Headline Above Video */}
                    <div className="space-y-4">
                        <Badge variant="destructive" className="mb-2">Video Revelación</Badge>
                        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-slate-900 leading-tight">
                            {headline}
                        </h1>
                    </div>

                    {/* Video Container */}
                    <div className="relative aspect-video bg-slate-900 rounded-xl overflow-hidden shadow-2xl mx-auto w-full max-w-3xl border-4 border-slate-100">
                        {video_url ? (
                            <iframe 
                                src={video_url} 
                                className="w-full h-full" 
                                allow="autoplay; fullscreen" 
                                allowFullScreen
                            />
                        ) : (
                            <div className="flex items-center justify-center h-full text-white flex-col gap-4">
                                <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                                    <ArrowRight className="w-8 h-8 text-white" />
                                </div>
                                <span className="font-medium text-slate-400">Video Placeholder</span>
                            </div>
                        )}
                    </div>

                    {/* CTA Below Video */}
                    <div className="pt-6 max-w-xl mx-auto space-y-4">
                        <Button 
                            size="lg" 
                            className="w-full text-xl py-8 rounded-lg shadow-xl animate-pulse"
                            style={{ backgroundColor: primaryColor }}
                        >
                            {cta_text} <ArrowRight className="ml-2 w-6 h-6" />
                        </Button>
                        <p className="text-sm text-slate-500 italic">{subheadline}</p>
                    </div>
                </div>
            </section>
        );
    }

    // 2. Urgency Layout (Countdown + Classic)
    if (layout === "urgency") {
        return (
            <div className="flex flex-col">
                {/* Sticky Urgency Bar */}
                <div className="bg-rose-600 text-white py-2 px-4 text-center font-bold text-sm md:text-base sticky top-0 z-50 shadow-md">
                   ⚠️ {scarcity_text || "¡Atención! Esta oferta expira pronto."}
                </div>
                
                {/* Classic Centered Hero below */}
                <section className="relative py-20 px-6 text-center bg-slate-50">
                    <div className="max-w-4xl mx-auto space-y-6">
                        <h1 className="text-4xl md:text-6xl font-black tracking-tight text-slate-900">
                            {headline}
                        </h1>
                        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                            {subheadline}
                        </p>
                        <div className="pt-6">
                             <Button size="lg" className="text-lg px-12 py-6 rounded-full" style={{ backgroundColor: primaryColor }}>
                                {cta_text}
                             </Button>
                        </div>
                    </div>
                </section>
            </div>
        );
    }
    
    // 3. Quiz Layout (Micro-commitment)
    if (layout === "quiz") {
         return (
            <section className="relative py-24 px-6 text-center bg-white">
                <div className="max-w-2xl mx-auto space-y-8 bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
                    <Badge variant="outline" className="mb-4">Evaluación Gratuita</Badge>
                    <h1 className="text-3xl md:text-4xl font-bold text-slate-900">
                        {headline}
                    </h1>
                    <p className="text-lg text-slate-600">
                        {subheadline}
                    </p>
                    
                    {/* Fake Quiz Options */}
                    <div className="grid gap-3 text-left mt-8">
                        {["Opción A: Principiante", "Opción B: Intermedio", "Opción C: Avanzado"].map((opt, i) => (
                            <button key={i} className="p-4 rounded-lg border border-slate-200 hover:border-blue-500 hover:bg-blue-50 transition-all font-medium text-slate-700 flex justify-between items-center group">
                                {opt}
                                <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity text-blue-500" />
                            </button>
                        ))}
                    </div>
                </div>
            </section>
        );
    }

    // 4. Background Layout (Immersive)
    if (layout === "background") {
        return (
            <section className="relative min-h-[600px] flex items-center justify-center text-center px-6 overflow-hidden">
                {/* Background Image with Overlay */}
                <div 
                    className="absolute inset-0 z-0 bg-cover bg-center"
                    style={{ backgroundImage: `url(${bgImage})` }}
                />
                <div className="absolute inset-0 bg-black/60 z-10" />
                
                <div className="relative z-20 max-w-4xl mx-auto space-y-8 text-white">
                    <Badge variant="outline" className="border-white/30 text-white bg-white/10 backdrop-blur-sm">
                        Oferta Exclusiva
                    </Badge>
                    <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-tight">
                        {headline}
                    </h1>
                    <p className="text-xl md:text-2xl text-slate-200 max-w-2xl mx-auto font-light">
                        {subheadline}
                    </p>
                    <div className="pt-8">
                        <Button 
                            size="lg" 
                            className="text-lg px-10 py-7 rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all bg-white text-slate-900 hover:bg-slate-100 border-none"
                        >
                            {cta_text} <ArrowRight className="ml-2 w-5 h-5" />
                        </Button>
                        {scarcity_text && (
                            <div className="mt-6 flex items-center justify-center gap-2 text-sm text-slate-300 font-medium bg-black/30 w-fit mx-auto px-4 py-1 rounded-full backdrop-blur-sm">
                                <Clock className="w-4 h-4" />
                                <span>{scarcity_text}</span>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        );
    }

    // 2. Split Layout (Text Left, Image Right)
    if (layout === "split") {
        return (
            <section className="relative py-24 px-6 overflow-hidden bg-white border-b border-slate-100">
                <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    {/* Left: Content */}
                    <div className="space-y-8 text-left order-2 lg:order-1">
                        <Badge variant="secondary" className="bg-slate-100 text-slate-600 hover:bg-slate-200">
                            Nuevo Programa
                        </Badge>
                        <div className="space-y-4">
                            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
                                {headline}
                            </h1>
                            <p className="text-lg md:text-xl text-slate-600 leading-relaxed max-w-lg">
                                {subheadline}
                            </p>
                        </div>
                        <div className="flex flex-col sm:flex-row gap-4 pt-4">
                            <Button 
                                size="lg" 
                                className="text-lg px-8 py-6 shadow-lg hover:shadow-xl transition-all"
                                style={{ backgroundColor: primaryColor }}
                            >
                                {cta_text} <ArrowRight className="ml-2 w-5 h-5" />
                            </Button>
                        </div>
                        {scarcity_text && (
                            <div className="flex items-center gap-2 text-sm text-amber-600 font-medium bg-amber-50 w-fit px-3 py-1 rounded-md">
                                <Clock className="w-4 h-4" />
                                <span>{scarcity_text}</span>
                            </div>
                        )}
                    </div>

                    {/* Right: Image */}
                    <div className="relative order-1 lg:order-2 h-[400px] lg:h-[600px] rounded-2xl overflow-hidden shadow-2xl rotate-1 hover:rotate-0 transition-transform duration-500">
                        <div 
                            className="absolute inset-0 bg-cover bg-center"
                            style={{ backgroundImage: `url(${bgImage})` }}
                        />
                        <div className="absolute inset-0 bg-gradient-to-tr from-black/20 to-transparent pointer-events-none" />
                    </div>
                </div>
            </section>
        );
    }

    // 3. Centered Layout (Default)
    return (
        <section className="relative py-24 px-6 text-center border-b border-slate-100 overflow-hidden bg-white">
            <div 
                className="absolute inset-0 opacity-[0.03] pointer-events-none" 
                style={{ backgroundColor: primaryColor }} 
            />
            <div className="max-w-4xl mx-auto space-y-8 relative z-10">
                <Badge variant="outline" className="mb-4 border-slate-300 text-slate-500 px-4 py-1">
                    Programa de Transformación
                </Badge>
                <div className="space-y-4">
                    <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-tight">
                        {headline}
                    </h1>
                    <p className="text-xl md:text-2xl text-slate-600 font-medium max-w-2xl mx-auto leading-relaxed">
                        {subheadline}
                    </p>
                </div>
                
                <div className="pt-8 flex flex-col items-center justify-center gap-4">
                     <Button 
                        size="lg" 
                        className="text-lg px-10 py-7 rounded-full shadow-xl hover:shadow-2xl hover:-translate-y-1 transition-all"
                        style={{ backgroundColor: primaryColor }}
                     >
                        {cta_text} <ArrowRight className="ml-2 w-5 h-5" />
                     </Button>
                     {scarcity_text && (
                        <div className="mt-2 flex items-center justify-center gap-2 text-sm text-slate-500 bg-slate-50 px-4 py-2 rounded-full border border-slate-100">
                            <Clock className="w-4 h-4" />
                            <span>{scarcity_text}</span>
                        </div>
                     )}
                </div>
            </div>
        </section>
    );
}