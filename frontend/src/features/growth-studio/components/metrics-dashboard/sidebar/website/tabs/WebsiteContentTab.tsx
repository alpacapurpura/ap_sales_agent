'use client';

import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { ChartInfoTooltip } from '../../shared/ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';
import type { WebsiteData } from '../types';

interface WebsiteContentTabProps {
  data: WebsiteData | undefined;
  isLoading: boolean;
}

export function WebsiteContentTab({ data, isLoading }: WebsiteContentTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const topPages = data.extraData?.top_pages;
  const maxViews = topPages && topPages.length > 0
    ? Math.max(...topPages.map(p => p.views), 1)
    : 1;

  return (
    <div className="space-y-8">
      {/* Top Pages Table */}
      <ChartSection slug="paginas-top">
        <div className="space-y-3">
          <ChartInfoTooltip
            title="Páginas más visitadas"
            description="Las páginas que reciben más tráfico. Optimiza estas páginas primero para maximizar conversiones. Si tu landing page no está en el top 3, revisa tu estructura de navegación."
          />
          {topPages && topPages.length > 0 ? (
            <div className="rounded-lg border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground w-8">
                      #
                    </th>
                    <th className="px-3 py-2 text-left font-medium text-muted-foreground">
                      Página
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-muted-foreground w-20">
                      Vistas
                    </th>
                    <th className="px-3 py-2 text-right font-medium text-muted-foreground w-16">
                      % Total
                    </th>
                    <th className="px-3 py-2 w-24" aria-label="Barra de proporción" />
                  </tr>
                </thead>
                <tbody>
                  {topPages.slice(0, 10).map((page, i) => (
                    <tr
                      key={page.path}
                      className={cn(
                        'border-b last:border-b-0 transition-colors hover:bg-muted/30',
                      )}
                    >
                      <td className="px-3 py-2 text-muted-foreground tabular-nums">
                        {i + 1}
                      </td>
                      <td className="px-3 py-2">
                        <span className="text-blue-600 dark:text-blue-400 font-mono text-xs truncate block max-w-[240px]">
                          {page.path}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right font-medium tabular-nums">
                        {page.views.toLocaleString('en-US')}
                      </td>
                      <td className="px-3 py-2 text-right text-muted-foreground tabular-nums">
                        {page.percentage.toFixed(1)}%
                      </td>
                      <td className="px-3 py-2">
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full rounded-full bg-blue-500/70 transition-all"
                            // Inline style required for dynamic percentage width
                            style={{
                              width: `${Math.max((page.views / maxViews) * 100, 2)}%`,
                            }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
              Datos disponibles próximamente
            </div>
          )}
        </div>
      </ChartSection>

      {/* Exit Pages Placeholder */}
      <ChartSection slug="paginas-salida">
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Páginas de Salida"
            description="Las últimas páginas que ven los usuarios antes de irse. Si tu página de ventas aparece aquí, revisa la propuesta de valor y el CTA."
          />
          <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
            Próximamente
          </div>
        </div>
      </ChartSection>

      {/* Events Summary Placeholder */}
      <ChartSection slug="eventos">
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Resumen de Eventos"
            description="Eventos clave rastreados en tu sitio: clics en botones, reproducciones de video, descargas, envíos de formulario."
          />
          <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
            Próximamente
          </div>
        </div>
      </ChartSection>
    </div>
  );
}
