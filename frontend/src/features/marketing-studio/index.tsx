import React from 'react';
import StrategyCanvas from './components/strategy-canvas/StrategyCanvas';
import { MOCK_CONFIG } from './components/strategy-canvas/config/mock-data';

export default function MarketingStudio() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Strategy Canvas</h2>
          <p className="text-muted-foreground">
            Visualiza y optimiza tu embudo de conversión de extremo a extremo.
          </p>
        </div>
      </div>
      
      <div className="rounded-xl border bg-card text-card-foreground shadow">
        <div className="p-6 pt-0">
          <div className="h-[800px] w-full mt-6">
            <StrategyCanvas config={MOCK_CONFIG} />
          </div>
        </div>
      </div>
    </div>
  );
}
