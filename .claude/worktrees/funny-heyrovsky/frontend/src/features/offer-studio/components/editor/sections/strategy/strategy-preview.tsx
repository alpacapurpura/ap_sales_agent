import React from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { OfferFormValues } from '../../../../types/schema';
import { User, Target, AlertCircle } from 'lucide-react';
import { useFormContext } from 'react-hook-form';

interface StrategyPreviewProps {
  data?: Partial<OfferFormValues>;
}

export const StrategyPreview = ({ data: propsData }: StrategyPreviewProps) => {
  // Try to get data from props, fallback to form context if available
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);

  if (!data) {
    return (
      <div className="text-muted-foreground text-sm p-4 border border-dashed rounded-md flex items-center justify-center h-full">
        No hay datos disponibles para previsualizar
      </div>
    );
  }

  const { avatar_id, marketing_pain_points, marketing_desires } = data;
  
  // Prioritize pain points, fallback to desires
  const highlights = (marketing_pain_points && marketing_pain_points.length > 0) 
    ? marketing_pain_points 
    : (marketing_desires || []);
    
  const displayHighlights = highlights.slice(0, 3);
  const hasHighlights = displayHighlights.length > 0;
  const isPainPoints = marketing_pain_points && marketing_pain_points.length > 0;

  return (
    <div className="w-full flex flex-col sm:flex-row gap-6 p-4">
      {/* Avatar Section */}
      <div className="flex flex-col items-center sm:items-start min-w-[120px] gap-3 shrink-0">
        <div className="relative">
          <Avatar className="h-16 w-16 border-2 border-background shadow-sm bg-muted">
            <AvatarFallback className="bg-primary/5 text-primary">
              <User className="h-8 w-8" />
            </AvatarFallback>
          </Avatar>
        </div>
        <div className="text-center sm:text-left">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
            Avatar Objetivo
          </p>
          <p className="text-sm font-semibold text-foreground">
            {avatar_id ? (
              <span className="font-mono text-xs bg-muted px-1.5 py-0.5 rounded">{avatar_id.substring(0, 8)}...</span>
            ) : (
              <span className="text-muted-foreground italic text-xs">No seleccionado</span>
            )}
          </p>
        </div>
      </div>

      {/* Highlights Section */}
      <div className="flex-1 flex flex-col justify-center min-h-[80px]">
        {hasHighlights ? (
          <div className="flex flex-wrap gap-2 content-center justify-center sm:justify-start">
            {displayHighlights.map((point, index) => (
              <div 
                key={index} 
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/40 text-secondary-foreground text-sm border border-transparent hover:border-border/50 transition-colors"
              >
                {isPainPoints ? (
                  <AlertCircle className="w-3.5 h-3.5 text-destructive/70 shrink-0" />
                ) : (
                  <Target className="w-3.5 h-3.5 text-primary/70 shrink-0" />
                )}
                <span className="truncate max-w-[200px] sm:max-w-xs font-medium">{point}</span>
              </div>
            ))}
          </div>
        ) : (
            <div className="flex items-center justify-center sm:justify-start h-full text-muted-foreground text-sm italic">
                Sin puntos de dolor definidos
            </div>
        )}
      </div>
    </div>
  );
};
