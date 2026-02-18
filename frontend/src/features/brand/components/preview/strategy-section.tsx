import { BrandStrategy, BrandVisuals } from "@/features/brand/types";
import { cn } from "@/lib/utils";
import { Target, Trophy, ShieldAlert, Swords } from "lucide-react";

interface StrategySectionProps {
    strategy: BrandStrategy;
    visuals: BrandVisuals;
    onEdit: () => void;
}

export function StrategySection({ strategy, visuals, onEdit }: StrategySectionProps) {
    const hasContent = strategy?.unique_value_proposition || (strategy?.competitors && strategy.competitors.length > 0);

    return (
        <section 
            onClick={onEdit}
            className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
        >
            {/* Header / Label */}
            <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
                <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
                    <Target className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold uppercase tracking-wider">Estrategia & Posicionamiento</h3>
            </div>

            {!hasContent ? (
                <div className="pl-0 md:pl-14">
                    <p className="text-lg text-muted-foreground italic mb-2">
                        &quot;El posicionamiento no es lo que haces a un producto. El posicionamiento es lo que haces a la mente del prospecto.&quot;
                    </p>
                    <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                        <Swords className="w-4 h-4" />
                        Definir Estrategia Competitiva
                    </span>
                </div>
            ) : (
                <div className="pl-0 md:pl-14 grid gap-8">
                    {/* UVP */}
                    <div>
                        <h4 className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-3">
                            <Trophy className="w-4 h-4 text-amber-500" />
                            Propuesta de Valor Única
                        </h4>
                        <p className="text-base font-serif text-foreground leading-relaxed">
                            {strategy.unique_value_proposition || "No definida."}
                        </p>
                    </div>

                    {/* Competitors */}
                    {strategy.competitors && strategy.competitors.length > 0 && (
                        <div>
                            <h4 className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-3">
                                <ShieldAlert className="w-4 h-4 text-red-400" />
                                Paisaje Competitivo
                            </h4>
                            <div className="flex flex-col gap-2">
                                {strategy.competitors.map(comp => (
                                    <div key={comp.id} className="flex flex-col md:flex-row md:items-baseline gap-1 md:gap-2">
                                        <span className="font-bold text-foreground min-w-[120px]">{comp.name}:</span>
                                        <span className="text-muted-foreground text-sm">{comp.differentiation}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </section>
    );
}
