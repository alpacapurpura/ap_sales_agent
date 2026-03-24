'use client';

import { Clock } from 'lucide-react';
import type { OfferHealthData } from '../../../types/metrics';

interface OfferHealthCardProps {
  offer: OfferHealthData;
}

export function OfferHealthCard({ offer }: OfferHealthCardProps) {
  const isHealthy = offer.healthPct >= 60;

  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm hover:border-emerald-300 dark:hover:border-emerald-700 hover:shadow-md transition-all group relative overflow-hidden h-full flex flex-col">
      <div className={`absolute top-0 left-0 w-1 h-full transition-colors bg-slate-200 dark:bg-slate-700 ${isHealthy ? 'group-hover:bg-emerald-400' : 'group-hover:bg-amber-400'}`}></div>
      
      <div className="flex justify-between items-start mb-3">
        <div className="pl-2 flex-1">
          <h5 className="font-semibold text-sm text-foreground line-clamp-2" title={offer.publicName}>{offer.publicName}</h5>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-1">{offer.totalCustomers} Clientes Totales</p>
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium shrink-0 ml-2 ${
            isHealthy
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800'
              : 'bg-amber-50 text-amber-700 border border-amber-100 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800'
          }`}
        >
          {isHealthy ? 'Saludable' : 'Atención'}
        </span>
      </div>

      <div className="pl-2 space-y-3 flex-1 flex flex-col justify-end">
        <div className="flex items-center justify-between text-xs">
          <div className="flex gap-3">
            <span className="text-emerald-600 dark:text-emerald-500 font-medium">{offer.activeCount} Activos</span>
            <span className="text-muted-foreground">{offer.inactiveCount} Inactivos</span>
          </div>
          <span className="font-bold text-foreground">{offer.healthPct.toFixed(0)}% Salud</span>
        </div>
        
        <div className="w-full h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden flex">
          <div className={`h-full ${isHealthy ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${offer.healthPct}%` }}></div>
        </div>
        
        {offer.ttvDays != null && (
          <div className="pt-2 border-t border-border mt-auto">
            <p className="text-[10px] text-muted-foreground flex items-center">
              <Clock className="w-3 h-3 mr-1" /> 
              Tiempo de activación: {Math.round(offer.ttvDays)} {Math.round(offer.ttvDays) === 1 ? 'día' : 'días'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
