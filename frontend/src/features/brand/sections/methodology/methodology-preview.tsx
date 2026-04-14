import { BrandStrategy, BrandVisuals } from "@/features/brand/types";
import { Lightbulb, GraduationCap } from "lucide-react";

interface MethodologySectionProps {
  strategy: BrandStrategy;
  visuals: BrandVisuals;
  onEdit: () => void;
}

export function MethodologySection({ strategy, visuals, onEdit }: MethodologySectionProps) {
  const pillars = strategy?.methodology_pillars || [];
  const hasContent = pillars.length > 0;

  return (
    <section
      onClick={onEdit}
      className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <GraduationCap className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Metodología & Pilares</h3>
      </div>

      {!hasContent ? (
        <div className="pl-0 md:pl-14">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;¿Cómo transformas a tus clientes? Tu método es tu producto.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Definir Metodología
          </span>
        </div>
      ) : (
        <div className="pl-0 md:pl-14">
          <h4 className="text-xl font-medium text-foreground mb-6">
            {strategy.methodology_name || "El Método"}
          </h4>

          {strategy.methodology_description && (
            <div className="mb-8 p-4 bg-muted/20 rounded-lg border-l-2 border-primary">
              <p className="text-sm text-muted-foreground leading-relaxed">
                {strategy.methodology_description}
              </p>
            </div>
          )}

          <ul className="space-y-6">
            {pillars.map((pillar, index) => (
              <li key={pillar.id} className="flex gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs font-bold">
                    {index + 1}
                  </div>
                </div>
                <div>
                  <h5 className="font-semibold text-foreground">{pillar.title}</h5>
                  {pillar.description && (
                    <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                      {pillar.description}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
