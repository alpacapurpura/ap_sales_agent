import React from 'react';
import { MetricsDashboard } from './components/metrics-dashboard';

export default function MarketingStudio() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Growth Studio</h2>
          <p className="text-muted-foreground">
            Entiende tu negocio de un vistazo
          </p>
        </div>
      </div>

      <MetricsDashboard />
    </div>
  );
}
