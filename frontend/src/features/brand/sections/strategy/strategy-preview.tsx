import { BrandStrategy, BrandVisuals } from "@/features/brand/types";
import { Target, Swords } from "lucide-react";

interface StrategySectionProps {
    strategy: BrandStrategy;
    visuals: BrandVisuals;
    onEdit: () => void;
}

/**
 * @deprecated This component is no longer used in the layout.
 * Methodology is shown via MethodologySection, UVP via DifferentiationPreview,
 * and competitors via MarketPreview.
 */
export function StrategySection({ strategy, visuals, onEdit }: StrategySectionProps) {
    const hasContent = !!strategy?.methodology_name;

    return (
        <section
            onClick={onEdit}
            className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
        >
            <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
                <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
                    <Target className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold uppercase tracking-wider">Metodologia</h3>
            </div>

            {!hasContent ? (
                <div className="pl-0 md:pl-14">
                    <p className="text-lg text-muted-foreground italic mb-2">
                        &quot;Sin metodologia no hay proceso repetible.&quot;
                    </p>
                    <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                        <Swords className="w-4 h-4" />
                        Definir Metodologia
                    </span>
                </div>
            ) : (
                <div className="pl-0 md:pl-14">
                    <p className="text-base font-serif text-foreground leading-relaxed">
                        {strategy.methodology_name}
                    </p>
                    {strategy.methodology_description && (
                        <p className="text-sm text-muted-foreground mt-2">{strategy.methodology_description}</p>
                    )}
                </div>
            )}
        </section>
    );
}
