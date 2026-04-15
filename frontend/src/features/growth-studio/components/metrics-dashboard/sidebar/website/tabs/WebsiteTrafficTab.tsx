"use client";

import { Loader2 } from "lucide-react";
import { Cell, Pie, PieChart, Tooltip as RechartsTooltip } from "recharts";

import { ChartContainer } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

import { ChartInfoTooltip } from "../../shared/ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";

import type { WebsiteData } from "../types";

const SOURCE_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(210 40% 60%)",
  "hsl(280 40% 60%)",
];

const DEVICE_COLORS: Record<string, string> = {
  desktop: "bg-blue-500",
  mobile: "bg-emerald-500",
  tablet: "bg-amber-500",
};

const DEVICE_LABELS: Record<string, string> = {
  desktop: "Escritorio",
  mobile: "Móvil",
  tablet: "Tablet",
};

const COUNTRY_FLAGS: Record<string, string> = {
  US: "🇺🇸",
  MX: "🇲🇽",
  CO: "🇨🇴",
  AR: "🇦🇷",
  ES: "🇪🇸",
  CL: "🇨🇱",
  PE: "🇵🇪",
  BR: "🇧🇷",
  EC: "🇪🇨",
  VE: "🇻🇪",
};

interface WebsiteTrafficTabProps {
  data: WebsiteData | undefined;
  isLoading: boolean;
}

export function WebsiteTrafficTab({ data, isLoading }: WebsiteTrafficTabProps) {
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

  const trafficSources = data.extraData?.traffic_sources;
  const deviceSplit = data.extraData?.device_split;
  const countries = data.extraData?.country;

  // Compute new vs returning from KPIs
  const usersKpi = data.kpis.find((k) => k.metricName === "users");
  const newUsersKpi = data.kpis.find((k) => k.metricName === "newUsers");
  const totalUsers = usersKpi?.currentValue ?? 0;
  const newUsers = newUsersKpi?.currentValue ?? 0;
  const returningUsers = totalUsers > 0 ? totalUsers - newUsers : 0;
  const newUsersPct = totalUsers > 0 ? (newUsers / totalUsers) * 100 : 0;
  const returningPct = totalUsers > 0 ? (returningUsers / totalUsers) * 100 : 0;

  const hasExtraData = trafficSources || deviceSplit || countries;

  return (
    <div className="space-y-8">
      {/* Traffic Sources Donut */}
      {trafficSources && trafficSources.length > 0 ? (
        <ChartSection slug="fuentes-trafico">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Fuentes de Tráfico"
              description="De dónde vienen tus visitantes. Orgánico = SEO, Directo = URL directa, Social = redes sociales, Referral = otros sitios. Diversificar fuentes reduce riesgo."
            />
            <div className="flex items-center gap-6">
              <ChartContainer config={{}} className="h-[200px] w-[200px] !aspect-auto">
                <PieChart>
                  <Pie
                    data={trafficSources.map((s) => ({ name: s.source, value: s.sessions }))}
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {trafficSources.map((_, i) => (
                      <Cell key={i} fill={SOURCE_COLORS[i % SOURCE_COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ChartContainer>
              <div className="space-y-2">
                {trafficSources.map((s, i) => (
                  <div key={s.source} className="flex items-center gap-2 text-sm">
                    <span
                      className="h-3 w-3 rounded-sm shrink-0"
                      // Inline style required for dynamic chart colors from array
                      style={{ backgroundColor: SOURCE_COLORS[i % SOURCE_COLORS.length] }}
                    />
                    <span className="text-muted-foreground capitalize">{s.source}</span>
                    <span className="font-medium tabular-nums ml-auto">
                      {s.percentage.toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ChartSection>
      ) : (
        !hasExtraData && (
          <ChartSection slug="fuentes-trafico">
            <div className="space-y-2">
              <ChartInfoTooltip
                title="Fuentes de Tráfico"
                description="De dónde vienen tus visitantes."
              />
              <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
                Datos disponibles próximamente
              </div>
            </div>
          </ChartSection>
        )
      )}

      {/* Device Split */}
      {deviceSplit && deviceSplit.length > 0 ? (
        <ChartSection slug="dispositivos">
          <div className="space-y-3">
            <ChartInfoTooltip
              title="Dispositivos"
              description="Distribución de tráfico por tipo de dispositivo. Si la mayoría es móvil, asegúrate de que tu sitio se vea bien en celulares."
            />
            <div className="space-y-2">
              {deviceSplit.map((d) => (
                <div key={d.device} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {DEVICE_LABELS[d.device] ?? d.device}
                    </span>
                    <span className="font-medium tabular-nums">{d.percentage.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all",
                        DEVICE_COLORS[d.device] ?? "bg-gray-400",
                      )}
                      // Inline style required for dynamic percentage width
                      style={{ width: `${Math.max(d.percentage, 1)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ChartSection>
      ) : null}

      {/* New vs Returning */}
      {totalUsers > 0 && (
        <ChartSection slug="nuevos-vs-recurrentes">
          <div className="space-y-3">
            <ChartInfoTooltip
              title="Nuevos vs Recurrentes"
              description="Proporción de visitantes nuevos contra recurrentes. Un balance sano es 60-70% nuevos. Si los recurrentes son muy bajos, tu contenido no genera lealtad."
            />
            <div className="space-y-2">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Nuevos</span>
                  <div className="flex items-center gap-2">
                    <span className="font-medium tabular-nums">
                      {newUsers.toLocaleString("en-US")}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({newUsersPct.toFixed(1)}%)
                    </span>
                  </div>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-blue-500 transition-all"
                    // Inline style required for dynamic percentage width
                    style={{ width: `${Math.max(newUsersPct, 1)}%` }}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Recurrentes</span>
                  <div className="flex items-center gap-2">
                    <span className="font-medium tabular-nums">
                      {returningUsers.toLocaleString("en-US")}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({returningPct.toFixed(1)}%)
                    </span>
                  </div>
                </div>
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-500 transition-all"
                    // Inline style required for dynamic percentage width
                    style={{ width: `${Math.max(returningPct, 1)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </ChartSection>
      )}

      {/* Country/Region Bars */}
      {countries && countries.length > 0 ? (
        <ChartSection slug="paises">
          <div className="space-y-3">
            <ChartInfoTooltip
              title="Países / Regiones"
              description="Distribución geográfica de tus visitantes. Útil para segmentar campañas y adaptar contenido por región."
            />
            <div className="space-y-2">
              {countries.slice(0, 8).map((c) => {
                const flag = COUNTRY_FLAGS[c.country] ?? "🌐";
                return (
                  <div key={c.country} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        {flag} {c.country}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="font-medium tabular-nums">
                          {c.sessions.toLocaleString("en-US")}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          ({c.percentage.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-blue-500/70 transition-all"
                        // Inline style required for dynamic percentage width
                        style={{ width: `${Math.max(c.percentage, 1)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </ChartSection>
      ) : null}

      {/* Fallback when no extra data at all */}
      {!hasExtraData && totalUsers === 0 && (
        <div className="rounded-lg border border-dashed p-12 text-center text-sm text-muted-foreground">
          Datos de tráfico disponibles próximamente
        </div>
      )}
    </div>
  );
}
