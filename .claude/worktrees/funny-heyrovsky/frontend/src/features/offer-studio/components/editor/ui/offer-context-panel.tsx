import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { OfferFormValues } from "../../../types/schema";
import { OfferType } from "../../../types";
import { Avatar } from "@/lib/api/avatar";
import { OFFER_TYPE_METADATA } from "../../../types/offer-metadata";
import { ArrowRight, Lightbulb, CheckCircle2, AlertCircle, AlertTriangle, CheckCircle, PlaneTakeoff, Zap, Book, ChevronDown, ChevronUp, ExternalLink, Edit, Maximize2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetFooter
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
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { InstructorsWidget } from "../components/widgets/instructors-widget";

export type OfferPhase = 'context' | 'solution' | 'deal';

interface OfferContextPanelProps {
    phase: OfferPhase;
    formValues: OfferFormValues;
    avatars: Avatar[];
    isDirty?: boolean;
    onSave?: () => Promise<void>;
    onFieldChange?: (field: string, value: any) => void;
}

// --- VALIDATION LOGIC ---
interface ValidationItem {
    label: string;
    valid: boolean;
    phase: OfferPhase;
}

export interface ValidationResult {
    totalItems: number;
    completedItems: number;
    progress: number;
    missingItems: ValidationItem[];
    isValid: boolean;
}

export function getOfferValidationStatus(values: OfferFormValues): ValidationResult {
    const checks: ValidationItem[] = [
        // Phase 1: Context
        { label: "Nombre Público", valid: !!values.public_name && values.public_name.length > 3, phase: 'context' },
        { label: "Tipo de Oferta", valid: !!values.type, phase: 'context' },
        { label: "Avatar Match", valid: !!values.avatar_id, phase: 'context' },
        
        // Phase 2: Solution
        { label: "Gran Promesa (Headline)", valid: !!values.headline_promise && values.headline_promise.length > 10, phase: 'solution' },
        { label: "Resultado Tangible", valid: !!values.primary_outcome, phase: 'solution' },
        { label: "Tiempo al Valor", valid: !!values.time_to_value, phase: 'solution' },
        { label: "Stack de Valor (Entregables)", valid: values.deliverables && values.deliverables.length > 0, phase: 'solution' },
        
        // Date Checks for Events and Fixed Programs
        { 
            label: "Fechas Definidas", 
            valid: (() => {
                const details = values.specific_details as any;
                const isEvent = [OfferType.MASTERMIND_NETWORK, OfferType.LUXURY_RETREAT].includes(values.type);
                // Check string values of enum ProgramStructure
                const isFixedProgram = details?.structure_type === 'FIXED_COHORT' || details?.structure_type === 'CHALLENGE';
                
                if (isEvent || isFixedProgram) {
                    return !!details?.start_date && !!details?.end_date;
                }
                return true; // Not required
            })(), 
            phase: 'solution' 
        },
        
        // Phase 3: Deal
        { label: "Precios Configurados", valid: values.pricing_options && values.pricing_options.length > 0, phase: 'deal' },
        { label: "Mecanismo de Cierre", valid: !!values.onboarding_action, phase: 'deal' },
    ];

    const completed = checks.filter(c => c.valid).length;
    const missing = checks.filter(c => !c.valid);
    
    return {
        totalItems: checks.length,
        completedItems: completed,
        progress: Math.round((completed / checks.length) * 100),
        missingItems: missing,
        isValid: missing.length === 0
    };
}

// --- FLIGHT CHECK CARD COMPONENT ---
function FlightCheckCard({ status }: { status: ValidationResult }) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (status.isValid) {
        return (
            <Card className="bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900 mb-6">
                <CardHeader className="pb-2">
                    <CardTitle className="text-emerald-700 dark:text-emerald-400 flex items-center gap-2 text-base">
                        <PlaneTakeoff className="w-5 h-5" />
                        Lista para Despegue
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-xs text-emerald-600 dark:text-emerald-500">
                        Tu oferta cumple con todos los requisitos esenciales. ¡Es hora de lanzar!
                    </p>
                    <Progress value={100} className="h-2 mt-3 bg-emerald-200 dark:bg-emerald-900" indicatorClassName="bg-emerald-500" />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="bg-amber-50/50 dark:bg-amber-950/10 border-amber-200/50 dark:border-amber-900/50 mb-6 shadow-sm transition-all duration-300">
            <CardHeader 
                className="pb-3 pt-4 cursor-pointer hover:bg-amber-100/20 dark:hover:bg-amber-900/20 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex justify-between items-center mb-1">
                    <Badge variant="outline" className="bg-background text-xs font-mono">
                        Flight Check
                    </Badge>
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-amber-600 dark:text-amber-500">
                            {status.progress}% Ready
                        </span>
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-muted-foreground"/> : <ChevronDown className="w-4 h-4 text-muted-foreground"/>}
                    </div>
                </div>
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    Faltan {status.missingItems.length} requisitos
                </CardTitle>
                <Progress value={status.progress} className="h-1.5 mt-2 bg-amber-100 dark:bg-amber-900" indicatorClassName="bg-amber-500" />
            </CardHeader>
            
            {isExpanded && (
                <CardContent className="pb-4 pt-0 animate-in slide-in-from-top-2 fade-in duration-200">
                    <div className="pr-1 pt-2">
                        <ul className="space-y-2">
                            {status.missingItems.map((item, idx) => (
                                <li key={idx} className="flex items-start gap-2 text-xs text-muted-foreground bg-background/50 p-2 rounded border border-transparent hover:border-amber-200 transition-colors cursor-help group">
                                    <AlertCircle className="w-3.5 h-3.5 mt-0.5 text-amber-500/70 group-hover:text-amber-500" />
                                    <div className="flex flex-col">
                                        <span className="font-medium text-foreground/80 group-hover:text-foreground">{item.label}</span>
                                        <span className="text-[10px] uppercase tracking-wider opacity-70">Fase: {item.phase}</span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </CardContent>
            )}
        </Card>
    );
}

export function OfferContextPanel({ phase, formValues, avatars, isDirty, onSave, onFieldChange }: OfferContextPanelProps) {
    const selectedAvatar = avatars.find(a => a.id === formValues.avatar_id);
    const offerTypeMeta = formValues.type ? OFFER_TYPE_METADATA[formValues.type] : null;
    const validationStatus = getOfferValidationStatus(formValues);

    return (
        <div className="h-full bg-muted/30 border-l hidden lg:flex flex-col overflow-hidden">
            <ScrollArea className="h-full">
                <div className="p-6 min-h-full">
                    {/* 1. FLIGHT CHECK STICKY AT TOP */}
                    <div className="sticky top-0 z-10 -mx-2 px-2 pb-6 bg-muted/30/95 backdrop-blur-[2px]">
                        <FlightCheckCard status={validationStatus} />
                    </div>

                    {/* 2. CONTEXTUAL CONTENT */}
                    <div className="pb-10">
                        {phase === 'context' && (
                            <ContextPhaseContent 
                                values={formValues} 
                                avatar={selectedAvatar} 
                                offerTypeMeta={offerTypeMeta} 
                                isDirty={isDirty}
                                onSave={onSave}
                                onFieldChange={onFieldChange}
                            />
                        )}
                        {phase === 'solution' && (
                            <SolutionPhaseContent 
                                values={formValues} 
                                offerTypeMeta={offerTypeMeta} 
                            />
                        )}
                        {phase === 'deal' && (
                            <DealPhaseContent 
                                values={formValues} 
                            />
                        )}
                    </div>
                </div>
            </ScrollArea>
        </div>
    );
}

// PHASE 1: CONTEXT CONTENT
function ContextPhaseContent({ 
    values, 
    avatar, 
    offerTypeMeta,
    isDirty,
    onSave,
    onFieldChange
}: { 
    values: OfferFormValues, 
    avatar?: Avatar, 
    offerTypeMeta: any,
    isDirty?: boolean,
    onSave?: () => Promise<void>,
    onFieldChange?: (field: string, value: any) => void
}) {
    const router = useRouter();
    const [showSaveAlert, setShowSaveAlert] = useState(false);

    // Identify Knowledge/Mentorship Offers
    const isKnowledgeOffer = [
        OfferType.HYBRID_MENTORSHIP,
        OfferType.COHORT_BASED_COURSE,
        OfferType.GROUP_COACHING_PROGRAM,
        OfferType.ONE_ON_ONE_PRIVATE_MENTORING,
        OfferType.MASTERMIND_NETWORK,
        OfferType.VIP_DAY_STRATEGY,
        OfferType.CORPORATE_TRAINING,
        OfferType.KEYNOTE_SPEAKING
    ].includes(values.type as OfferType);

    const handleEditClick = async () => {
        if (!avatar) return;

        if (isDirty && onSave) {
            setShowSaveAlert(true);
        } else {
            router.push(`/avatars/${avatar.id}/edit`);
        }
    };

    const handleConfirmSaveAndEdit = async () => {
        if (onSave) {
            await onSave();
            if (avatar) {
                router.push(`/avatars/${avatar.id}/edit`);
            }
        }
        setShowSaveAlert(false);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 pb-10">
            <div>
                <h3 className="text-lg font-semibold text-primary mb-2 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5" />
                    Estrategia & Identidad
                </h3>
                <p className="text-sm text-muted-foreground">
                    Definir claramente <strong>quién compra</strong> y <strong>por qué</strong> es el 80% del éxito.
                </p>
            </div>

            {/* INSTRUCTORS WIDGET (Read Only Preview) */}
            {isKnowledgeOffer && values.instructors && values.instructors.length > 0 && (
                <InstructorsWidget 
                    selectedInstructorIds={values.instructors}
                />
            )}

            {/* Avatar Card Preview with Sheet */}
            <Card className="bg-background border-primary/20 shadow-sm overflow-hidden">
                <div className="h-2 bg-primary/20 w-full" />
                <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                        <Badge variant="outline" className="mb-2">Target Avatar</Badge>
                        {avatar?.scope === 'OFFER_SPECIFIC' && <Badge className="text-[10px]">Específico</Badge>}
                    </div>
                    <CardTitle className="text-lg">{avatar?.name || "Sin Avatar Seleccionado"}</CardTitle>
                    <CardDescription className="line-clamp-3 text-xs mt-1">
                        {avatar?.icp_description || "Selecciona un avatar para ver sus detalles psicográficos."}
                    </CardDescription>
                </CardHeader>
                {avatar && (
                    <CardContent className="bg-muted/50 p-4 text-xs space-y-2 border-t">
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <span className="font-semibold block text-muted-foreground">Nivel de Conciencia</span>
                                {avatar.awareness_level}
                            </div>
                            <div>
                                <span className="font-semibold block text-muted-foreground">Sofisticación</span>
                                {avatar.sophistication_level}
                            </div>
                        </div>

                        <div className="flex gap-2 mt-4 pt-2 border-t">
                             {/* SHEET: VER COMPLETO */}
                             <Sheet>
                                <SheetTrigger asChild>
                                    <Button variant="outline" size="sm" className="w-full text-xs h-8">
                                        <Maximize2 className="w-3 h-3 mr-2" />
                                        Ver Completo
                                    </Button>
                                </SheetTrigger>
                                <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
                                    <SheetHeader>
                                        <SheetTitle className="flex items-center gap-2">
                                            {avatar.name}
                                            {avatar.is_default && <Badge variant="secondary">Default</Badge>}
                                        </SheetTitle>
                                        <SheetDescription>
                                            Perfil detallado del cliente ideal.
                                        </SheetDescription>
                                    </SheetHeader>
                                    
                                    <div className="space-y-6 py-6">
                                        <div className="space-y-2">
                                            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Descripción ICP</h4>
                                            <p className="text-sm leading-relaxed whitespace-pre-wrap bg-muted/30 p-3 rounded-md border">
                                                {avatar.icp_description || "Sin descripción definida."}
                                            </p>
                                        </div>

                                        {avatar.anti_avatar && (
                                            <div className="space-y-2">
                                                <h4 className="text-sm font-medium text-destructive/80 uppercase tracking-wider flex items-center gap-2">
                                                    <AlertCircle className="w-4 h-4" /> Anti-Avatar (A quién NO vender)
                                                </h4>
                                                <p className="text-sm leading-relaxed whitespace-pre-wrap bg-destructive/10 p-3 rounded-md border border-destructive/20 text-destructive-foreground/80">
                                                    {avatar.anti_avatar}
                                                </p>
                                            </div>
                                        )}

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded border">
                                                <span className="block text-xs font-semibold text-muted-foreground mb-1">Nivel de Conciencia</span>
                                                <span className="text-sm font-medium">{avatar.awareness_level}</span>
                                            </div>
                                            <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded border">
                                                <span className="block text-xs font-semibold text-muted-foreground mb-1">Nivel de Sofisticación</span>
                                                <span className="text-sm font-medium">{avatar.sophistication_level}</span>
                                            </div>
                                        </div>

                                        {avatar.voice_tone_config && Object.keys(avatar.voice_tone_config).length > 0 && (
                                            <div className="space-y-2">
                                                <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Voz y Tono</h4>
                                                <pre className="text-xs bg-slate-950 text-slate-50 p-3 rounded-md overflow-x-auto">
                                                    {JSON.stringify(avatar.voice_tone_config, null, 2)}
                                                </pre>
                                            </div>
                                        )}
                                    </div>

                                    <SheetFooter className="flex-col sm:flex-row gap-2">
                                        <Button onClick={handleEditClick} className="w-full sm:w-auto">
                                            <Edit className="w-4 h-4 mr-2" />
                                            Editar Avatar
                                        </Button>
                                    </SheetFooter>
                                </SheetContent>
                             </Sheet>
                        </div>
                    </CardContent>
                )}
            </Card>
            
            {/* Button to edit below card as requested */}
            {avatar && (
                <div className="flex justify-end">
                    <Button 
                        variant="ghost" 
                        size="sm" 
                        className="text-xs text-muted-foreground hover:text-primary"
                        onClick={handleEditClick}
                    >
                        <Edit className="w-3 h-3 mr-1" /> Editar {avatar.name}
                    </Button>
                </div>
            )}

            {/* ALERT DIALOG FOR UNSAVED CHANGES */}
            <AlertDialog open={showSaveAlert} onOpenChange={setShowSaveAlert}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Tienes cambios sin guardar</AlertDialogTitle>
                        <AlertDialogDescription>
                            Has modificado la oferta actual. Si sales ahora para editar el avatar, podrías perder tu progreso.
                            ¿Quieres guardar los cambios antes de ir al editor de avatar?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction onClick={handleConfirmSaveAndEdit}>Guardar y Editar</AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Pain Points Guide */}
            <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg border border-blue-100 dark:border-blue-900">
                <h4 className="font-medium text-blue-700 dark:text-blue-300 text-sm mb-2">Tips de Psicología</h4>
                <ul className="text-xs space-y-2 text-muted-foreground">
                    <li className="flex gap-2">
                        <CheckCircle2 className="w-3 h-3 mt-0.5 text-blue-500" />
                        Usa palabras viscerales (&quot;Miedo a quebrar&quot; vs &quot;Problemas financieros&quot;).
                    </li>
                    <li className="flex gap-2">
                        <CheckCircle2 className="w-3 h-3 mt-0.5 text-blue-500" />
                        El deseo debe ser el opuesto exacto del dolor principal.
                    </li>
                </ul>
            </div>
            
            {values.marketing_pain_points?.length > 0 && (
                <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase text-muted-foreground">Dolores Identificados</h4>
                    <div className="flex flex-wrap gap-1">
                         {values.marketing_pain_points.map((p, i) => (
                             <Badge key={i} variant="secondary" className="text-[10px] font-normal">{p}</Badge>
                         ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// PHASE 2: SOLUTION CONTENT
function SolutionPhaseContent({ values, offerTypeMeta }: { values: OfferFormValues, offerTypeMeta: any }) {
    const hasPromise = values.headline_promise && values.headline_promise.length > 10;
    
    // Resources Logic
    const assets = values.assets || [];
    const salesAssets = assets.filter(a => !a.is_knowledge_base);
    const knowledgeDocs = assets.filter(a => a.is_knowledge_base);
    
    const hasAssets = assets.length > 0;
    const isEquipped = salesAssets.length > 0 && knowledgeDocs.length > 0;

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 pb-10">
            <div>
                <h3 className="text-lg font-semibold text-primary mb-2 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5" />
                    Construcción de Oferta
                </h3>
                <p className="text-sm text-muted-foreground">
                    La promesa atrae, pero el mecanismo (el vehículo) justifica la compra.
                </p>
            </div>

            {/* NEW: Agent Capabilities Card (Before/During/After UX) */}
            <Card className={cn("border-l-4 transition-colors duration-500", 
                !hasAssets ? "bg-slate-50 border-slate-300 dark:bg-slate-900/50" : 
                isEquipped ? "bg-indigo-50 border-indigo-500 dark:bg-indigo-950/30" : "bg-blue-50 border-blue-400 dark:bg-blue-950/30"
            )}>
                <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                        <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <Zap className={cn("w-4 h-4", isEquipped ? "text-indigo-600 fill-indigo-600" : "text-slate-400")} />
                            Nivel de Equipamiento
                        </CardTitle>
                        {isEquipped && <Badge variant="default" className="bg-indigo-600 text-[10px]">Listo para Batalla</Badge>}
                    </div>
                    <CardDescription className="text-xs">
                        {!hasAssets && "Tu agente está 'ciego' y 'mudo'. Solo puede prometer, no demostrar."}
                        {hasAssets && !isEquipped && "Mejorando... Sigue agregando recursos visuales y técnicos."}
                        {isEquipped && "¡Excelente! El agente tiene ojos (evidencia) y cerebro (manuales)."}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                     {/* Visual/Sales Progress */}
                     <div className="space-y-1">
                        <div className="flex justify-between text-muted-foreground">
                            <span className="flex items-center gap-1"><CheckCircle2 className={cn("w-3 h-3", salesAssets.length > 0 ? "text-emerald-500" : "text-slate-300")}/> Persuasión Visual</span>
                            <span>{salesAssets.length} activos</span>
                        </div>
                        <Progress value={Math.min(salesAssets.length * 33, 100)} className="h-1.5" indicatorClassName={salesAssets.length > 0 ? "bg-emerald-500" : "bg-slate-200"} />
                     </div>
                     
                     {/* Knowledge Progress */}
                     <div className="space-y-1">
                        <div className="flex justify-between text-muted-foreground">
                            <span className="flex items-center gap-1"><Book className={cn("w-3 h-3", knowledgeDocs.length > 0 ? "text-blue-500" : "text-slate-300")}/> Conocimiento Técnico</span>
                            <span>{knowledgeDocs.length} docs</span>
                        </div>
                         <Progress value={Math.min(knowledgeDocs.length * 50, 100)} className="h-1.5" indicatorClassName={knowledgeDocs.length > 0 ? "bg-blue-500" : "bg-slate-200"} />
                     </div>

                     {/* Dynamic Insight */}
                     <div className="pt-2 border-t mt-2">
                        <p className="italic text-muted-foreground">
                            {!hasAssets && "Tip: Sube un PDF técnico y el agente podrá responder '¿Cómo funciona X?' sin alucinar."}
                            {salesAssets.length > 0 && knowledgeDocs.length === 0 && "Bien con la evidencia. Ahora dale un manual técnico para que no invente respuestas."}
                            {knowledgeDocs.length > 0 && salesAssets.length === 0 && "Sabe mucho, pero es aburrido. Sube un video o imagen para cerrar ventas."}
                            {isEquipped && "Tu agente ahora es un vendedor experto con soporte de ingeniero."}
                        </p>
                     </div>
                </CardContent>
            </Card>

            {/* Offer Construct Preview */}
            <Card className="bg-background shadow-md border-l-4 border-l-primary">
                <CardHeader>
                    <Badge className="w-fit mb-2">{offerTypeMeta?.label || "Oferta Genérica"}</Badge>
                    <CardTitle className={cn("text-lg leading-tight", !hasPromise && "text-muted-foreground italic")}>
                        {values.headline_promise || "Tu Gran Promesa aparecerá aquí..."}
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                    {values.primary_outcome && (
                        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                            <CheckCircle2 className="w-4 h-4" />
                            <span className="font-medium">Resultado: {values.primary_outcome}</span>
                        </div>
                    )}
                    
                    <Separator />
                    
                    <div className="space-y-2">
                        <div className="text-xs font-semibold text-muted-foreground uppercase">El Vehículo (Delivery)</div>
                        <div className="text-xs">
                             {offerTypeMeta?.label} diseñado para entregar resultados en <span className="font-bold">{values.time_to_value || "X tiempo"}</span>.
                        </div>
                    </div>

                    {values.deliverables && values.deliverables.length > 0 && (
                        <div className="bg-muted rounded p-3 space-y-2">
                             <div className="text-xs font-semibold text-muted-foreground uppercase flex justify-between">
                                <span>Stack ({values.deliverables.length})</span>
                                <span>Valor</span>
                             </div>
                             <ul className="space-y-1">
                                {values.deliverables.slice(0, 3).map((d, i) => (
                                    <li key={i} className="text-xs flex justify-between">
                                        <span className="truncate max-w-[150px]">• {d.name || "Item sin nombre"}</span>
                                        <span className="text-muted-foreground">${d.value_stack_price}</span>
                                    </li>
                                ))}
                                {values.deliverables.length > 3 && (
                                    <li className="text-[10px] text-muted-foreground italic">+ {values.deliverables.length - 3} más...</li>
                                )}
                             </ul>
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="bg-amber-50 dark:bg-amber-950/20 p-4 rounded-lg border border-amber-100 dark:border-amber-900">
                <h4 className="font-medium text-amber-700 dark:text-amber-300 text-sm mb-2 flex gap-2">
                    <AlertCircle className="w-4 h-4" /> Check de Coherencia
                </h4>
                <p className="text-xs text-muted-foreground">
                    ¿El <strong>Vehículo</strong> que elegiste ({offerTypeMeta?.label}) es capaz de entregar la <strong>Promesa</strong> en el tiempo que indicaste?
                </p>
            </div>
        </div>
    );
}

// PHASE 3: DEAL CONTENT
function DealPhaseContent({ values }: { values: OfferFormValues }) {
    const mainPrice = values.pricing_options?.[0];

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500 pb-10">
            <div>
                <h3 className="text-lg font-semibold text-primary mb-2 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5" />
                    El Cierre (Checkout)
                </h3>
                <p className="text-sm text-muted-foreground">
                    Haz que decir &quot;SÍ&quot; sea estúpidamente fácil.
                </p>
            </div>

            {/* Checkout Preview */}
            <Card className="bg-background max-w-sm mx-auto shadow-lg transform scale-95 origin-top">
                <div className="bg-slate-100 dark:bg-slate-800 p-3 border-b flex items-center justify-center">
                     <span className="text-xs font-mono text-muted-foreground">checkout.preview.com</span>
                </div>
                <CardHeader className="text-center pb-2">
                    <CardTitle className="text-base">{values.public_name || "Nombre Oferta"}</CardTitle>
                    <CardDescription className="text-xs">Resumen del pedido</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {mainPrice ? (
                         <div className="flex justify-between items-end border-b pb-4">
                            <span className="text-sm font-medium">Total a pagar</span>
                            <div className="text-right">
                                 <span className="text-2xl font-bold block">
                                     {values.currency} {mainPrice.total_amount || "0.00"}
                                 </span>
                                 {mainPrice.number_of_installments > 1 && (
                                     <span className="text-[10px] text-muted-foreground">
                                         o {mainPrice.number_of_installments} pagos de {mainPrice.installment_amount}
                                     </span>
                                 )}
                            </div>
                         </div>
                    ) : (
                        <div className="border-b pb-4 text-center text-amber-600 text-xs">
                            <AlertCircle className="w-4 h-4 mx-auto mb-1"/>
                            Sin precio definido
                        </div>
                    )}

                     <div className="space-y-2">
                         <div className="flex gap-2 items-start">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5" />
                            <p className="text-xs text-muted-foreground text-left">
                                Garantía: <span className="font-medium text-foreground">{values.guarantee_type || "Estándar"}</span>
                            </p>
                         </div>
                         <div className="flex gap-2 items-start">
                            <ArrowRight className="w-4 h-4 text-primary mt-0.5" />
                            <p className="text-xs text-muted-foreground text-left">
                                Acceso Inmediato via {values.onboarding_action || "Email"}
                            </p>
                         </div>
                     </div>

                     <div className="pt-2">
                         <div className="w-full bg-primary h-9 rounded text-primary-foreground flex items-center justify-center text-sm font-medium">
                             Completar Orden
                         </div>
                         <p className="text-[10px] text-center text-muted-foreground mt-2 flex items-center justify-center gap-1">
                             <span className="w-2 h-2 bg-emerald-500 rounded-full"/> 
                             Pago 100% Seguro
                         </p>
                     </div>
                </CardContent>
            </Card>
        </div>
    );
}