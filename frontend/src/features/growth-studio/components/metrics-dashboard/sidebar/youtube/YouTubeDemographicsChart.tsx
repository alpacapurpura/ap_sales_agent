'use client';

import { Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useYoutubeDemographics, useYoutubeCountries } from '../../../../hooks/useYoutubeAnalytics';

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return n.toLocaleString('es-ES');
}

// Country code to flag emoji
function countryFlag(code: string): string {
  if (!code || code.length !== 2) return '';
  const offset = 127397;
  return String.fromCodePoint(...[...code.toUpperCase()].map(c => c.charCodeAt(0) + offset));
}

interface YouTubeDemographicsChartProps {
  enabled: boolean;
}

export function YouTubeDemographicsChart({ enabled }: YouTubeDemographicsChartProps) {
  const { data: demographics, isLoading: demoLoading } = useYoutubeDemographics(enabled);
  const { data: countries, isLoading: countryLoading } = useYoutubeCountries(enabled);

  if (demoLoading || countryLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Process demographics into stacked bar data by age group
  const ageGroups: Record<string, { male: number; female: number }> = {};
  if (demographics) {
    for (const d of demographics) {
      const age = d.ageGroup;
      if (!ageGroups[age]) ageGroups[age] = { male: 0, female: 0 };
      if (d.gender === 'male') ageGroups[age].male += d.viewerPercentage;
      else if (d.gender === 'female') ageGroups[age].female += d.viewerPercentage;
    }
  }

  const AGE_ORDER = ['age13-17', 'age18-24', 'age25-34', 'age35-44', 'age45-54', 'age55-64', 'age65-'];
  const AGE_LABELS: Record<string, string> = {
    'age13-17': '13-17',
    'age18-24': '18-24',
    'age25-34': '25-34',
    'age35-44': '35-44',
    'age45-54': '45-54',
    'age55-64': '55-64',
    'age65-': '65+',
  };

  const chartData = AGE_ORDER
    .filter(age => ageGroups[age])
    .map(age => ({
      name: AGE_LABELS[age] || age,
      Hombres: Math.round((ageGroups[age]?.male || 0) * 10) / 10,
      Mujeres: Math.round((ageGroups[age]?.female || 0) * 10) / 10,
    }));

  const topCountries = countries?.slice(0, 5) || [];
  const totalViews = topCountries.reduce((sum, c) => sum + c.views, 0) || 1;

  return (
    <div className="space-y-4">
      {/* Demographics chart */}
      {chartData.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">
            Edad y Genero
          </h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} unit="%" />
              <Tooltip formatter={(value: number) => [`${value}%`]} contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Bar dataKey="Hombres" stackId="a" fill="#3b82f6" radius={[0, 0, 0, 0]} />
              <Bar dataKey="Mujeres" stackId="a" fill="#ec4899" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Countries */}
      {topCountries.length > 0 && (
        <div>
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-2">
            Paises
          </h4>
          <div className="space-y-1.5">
            {topCountries.map((c) => {
              const pct = Math.round((c.views / totalViews) * 100);
              return (
                <div key={c.country} className="flex items-center gap-2 text-sm">
                  <span className="text-base">{countryFlag(c.country)}</span>
                  <span className="flex-1 text-xs">{c.country}</span>
                  <span className="text-xs tabular-nums font-medium">{formatNumber(c.views)}</span>
                  <span className="text-[10px] text-muted-foreground w-8 text-right">{pct}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {chartData.length === 0 && topCountries.length === 0 && (
        <p className="text-xs text-muted-foreground py-4 text-center">Sin datos de audiencia</p>
      )}
    </div>
  );
}
