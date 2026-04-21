"use client";

export const dynamic = "force-dynamic";

import {
  Users,
  Target,
  Mail,
  DollarSign,
  Repeat,
  Share2,
  ArrowRight,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Facebook,
  Instagram,
  Globe,
  CreditCard,
  Calendar,
  MousePointer2,
} from "lucide-react";
import React, { useState } from "react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// --- TYPES (Simplified for Playground) ---

type StageId =
  | "ATRACCION"
  | "CAPTURA"
  | "NUTRICION"
  | "OPORTUNIDAD"
  | "VENTAS"
  | "ADOPCION"
  | "EXPANSION"
  | "EVANGELIZACION";

interface StageSummary {
  id: StageId;
  label: string;
  description: string;
  mainKpi: { label: string; value: string | number };
  secondaryKpi: { label: string; value: string | number };
  hasDetail: boolean;
}

interface ChannelMetric {
  slug: string;
  name: string;
  metrics: { label: string; value: string }[];
  status: "connected" | "disconnected" | "warning" | "critical";
  icon: React.ElementType;
}

interface StageDetailData {
  groups: {
    title: string;
    summary: string;
    channels: ChannelMetric[];
  }[];
}

// --- MOCK DATA ---

const STAGES: StageSummary[] = [
  {
    id: "ATRACCION",
    label: "Atracción",
    description: "Tráfico y alcance",
    mainKpi: { label: "Visitantes", value: "12.5k" },
    secondaryKpi: { label: "Canales Activos", value: 4 },
    hasDetail: true,
  },
  {
    id: "CAPTURA",
    label: "Captura",
    description: "Conversión a Leads",
    mainKpi: { label: "Leads", value: 843 },
    secondaryKpi: { label: "Conversión", value: "6.7%" },
    hasDetail: true,
  },
  {
    id: "NUTRICION",
    label: "Nutrición",
    description: "Maduración de Leads",
    mainKpi: { label: "MQLs", value: 312 },
    secondaryKpi: { label: "Conversión", value: "37%" },
    hasDetail: true,
  },
  {
    id: "OPORTUNIDAD",
    label: "Oportunidad",
    description: "Leads Calificados",
    mainKpi: { label: "SQLs", value: 89 },
    secondaryKpi: { label: "Conversión", value: "28.5%" },
    hasDetail: true,
  },
  {
    id: "VENTAS",
    label: "Ventas",
    description: "Cierre de Clientes",
    mainKpi: { label: "Revenue", value: "$12,450" },
    secondaryKpi: { label: "Nuevos Clientes", value: 42 },
    hasDetail: true,
  },
  {
    id: "ADOPCION",
    label: "Adopción",
    description: "Éxito del Cliente",
    mainKpi: { label: "Salud", value: "94%" },
    secondaryKpi: { label: "Activos", value: 38 },
    hasDetail: true,
  },
  {
    id: "EXPANSION",
    label: "Expansión",
    description: "Upsell y Cross-sell",
    mainKpi: { label: "Net MRR", value: "+$2,100" },
    secondaryKpi: { label: "LTV Avg", value: "$850" },
    hasDetail: true,
  },
  {
    id: "EVANGELIZACION",
    label: "Evangelización",
    description: "Referidos",
    mainKpi: { label: "K-Factor", value: "1.2" },
    secondaryKpi: { label: "Referidos", value: 8 },
    hasDetail: true,
  },
];

const MOCK_DETAILS: Record<StageId, StageDetailData> = {
  ATRACCION: {
    groups: [
      {
        title: "Redes Sociales",
        summary: "Alcance: 45k | Engagement: 2.3%",
        channels: [
          {
            slug: "ig",
            name: "Instagram",
            icon: Instagram,
            status: "connected",
            metrics: [
              { label: "Seguidores", value: "12.4k" },
              { label: "Alcance", value: "22k" },
            ],
          },
          {
            slug: "fb",
            name: "Facebook",
            icon: Facebook,
            status: "connected",
            metrics: [
              { label: "Seguidores", value: "8.1k" },
              { label: "Alcance", value: "15k" },
            ],
          },
        ],
      },
      {
        title: "Publicidad Pagada",
        summary: "Gasto: $1,200 | ROAS: 3.4",
        channels: [
          {
            slug: "meta-ads",
            name: "Meta Ads",
            icon: Target,
            status: "connected",
            metrics: [
              { label: "Gasto", value: "$800" },
              { label: "Clicks", value: "1.2k" },
            ],
          },
          {
            slug: "google-ads",
            name: "Google Ads",
            icon: Globe,
            status: "warning",
            metrics: [
              { label: "Gasto", value: "$400" },
              { label: "Clicks", value: "350" },
            ],
          },
        ],
      },
    ],
  },
  CAPTURA: {
    groups: [
      {
        title: "Infraestructura Web",
        summary: "Visitas: 5k | Leads: 400",
        channels: [
          {
            slug: "website",
            name: "Sitio Web Principal",
            icon: Globe,
            status: "connected",
            metrics: [
              { label: "Visitas", value: "3.2k" },
              { label: "Leads", value: "250" },
            ],
          },
          {
            slug: "lp-webinar",
            name: "LP Webinar",
            icon: MousePointer2,
            status: "connected",
            metrics: [
              { label: "Visitas", value: "1.8k" },
              { label: "Leads", value: "150" },
            ],
          },
        ],
      },
      {
        title: "Lead Magnets",
        summary: "Descargas: 350",
        channels: [
          {
            slug: "ebook",
            name: "Ebook 7 Pasos",
            icon: ArrowRight,
            status: "connected",
            metrics: [{ label: "Descargas", value: "210" }],
          },
        ],
      },
    ],
  },
  NUTRICION: {
    groups: [
      {
        title: "Email Marketing",
        summary: "Open Rate: 42% | Click Rate: 5%",
        channels: [
          {
            slug: "newsletter",
            name: "Newsletter Semanal",
            icon: Mail,
            status: "connected",
            metrics: [
              { label: "Enviados", value: "12k" },
              { label: "Open Rate", value: "45%" },
            ],
          },
          {
            slug: "welcome-seq",
            name: "Secuencia Bienvenida",
            icon: Repeat,
            status: "connected",
            metrics: [
              { label: "Enviados", value: "400" },
              { label: "Open Rate", value: "62%" },
            ],
          },
        ],
      },
    ],
  },
  OPORTUNIDAD: {
    groups: [
      {
        title: "Calificación",
        summary: "Agendadas: 45 | Asistencia: 80%",
        channels: [
          {
            slug: "calendly",
            name: "Calendly Sales",
            icon: Calendar,
            status: "connected",
            metrics: [
              { label: "Agendadas", value: "45" },
              { label: "No-Show", value: "20%" },
            ],
          },
        ],
      },
    ],
  },
  VENTAS: {
    groups: [
      {
        title: "Pasarelas de Pago",
        summary: "Transacciones: 42 | Valor: $12,450",
        channels: [
          {
            slug: "stripe",
            name: "Stripe",
            icon: CreditCard,
            status: "connected",
            metrics: [
              { label: "Volumen", value: "$8,200" },
              { label: "Tx", value: "28" },
            ],
          },
          {
            slug: "paypal",
            name: "PayPal",
            icon: DollarSign,
            status: "connected",
            metrics: [
              { label: "Volumen", value: "$4,250" },
              { label: "Tx", value: "14" },
            ],
          },
        ],
      },
    ],
  },
  ADOPCION: {
    groups: [
      {
        title: "Salud del Cliente",
        summary: "Activos: 94%",
        channels: [
          {
            slug: "platform",
            name: "Uso de Plataforma",
            icon: Activity,
            status: "connected",
            metrics: [
              { label: "Login Diario", value: "85%" },
              { label: "Features", value: "4.2/usr" },
            ],
          },
        ],
      },
    ],
  },
  EXPANSION: {
    groups: [
      {
        title: "Upsells",
        summary: "Revenue: $2,100",
        channels: [
          {
            slug: "vip-upgrade",
            name: "Upgrade VIP",
            icon: TrendingUp,
            status: "connected",
            metrics: [
              { label: "Conversión", value: "12%" },
              { label: "Revenue", value: "$2,100" },
            ],
          },
        ],
      },
    ],
  },
  EVANGELIZACION: {
    groups: [
      {
        title: "Referidos",
        summary: "Nuevos Clientes: 8",
        channels: [
          {
            slug: "referral-prog",
            name: "Programa Embajadores",
            icon: Share2,
            status: "connected",
            metrics: [
              { label: "Links", value: "34" },
              { label: "Conv.", value: "23%" },
            ],
          },
        ],
      },
    ],
  },
};

// --- COMPONENTS ---

function StageCard({
  stage,
  isActive,
  onClick,
}: {
  stage: StageSummary;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <Card
      onClick={onClick}
      className={cn(
        "relative flex flex-col items-center justify-center p-4 min-w-[140px] cursor-pointer transition-all duration-200 select-none snap-center hover:scale-105",
        isActive
          ? "border-primary ring-2 ring-primary/20 shadow-lg bg-primary/5"
          : "hover:border-primary/50 hover:shadow-md",
      )}
    >
      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">
        {stage.label}
      </span>
      <div className="text-2xl font-bold tabular-nums text-foreground">{stage.mainKpi.value}</div>
      <div className="text-xs text-muted-foreground mb-1">{stage.mainKpi.label}</div>
      <div className="text-[10px] text-muted-foreground/70 bg-muted px-2 py-0.5 rounded-full">
        {stage.secondaryKpi.value} {stage.secondaryKpi.label}
      </div>

      {isActive && (
        <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-primary rotate-45 border-r border-b border-background" />
      )}
    </Card>
  );
}

function ChannelRow({ channel }: { channel: ChannelMetric }) {
  const Icon = channel.icon;

  return (
    <div className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-border/50">
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "p-2 rounded-md",
            channel.status === "connected"
              ? "bg-green-500/10 text-green-600"
              : channel.status === "warning"
                ? "bg-yellow-500/10 text-yellow-600"
                : "bg-muted text-muted-foreground",
          )}
        >
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-sm font-medium flex items-center gap-2">
            {channel.name}
            {channel.status === "warning" && <AlertCircle className="w-3 h-3 text-yellow-500" />}
          </div>
          <div className="text-xs text-muted-foreground">{channel.slug}</div>
        </div>
      </div>

      <div className="flex items-center gap-4 text-right">
        {channel.metrics.map((m, idx) => (
          <div key={idx} className="flex flex-col">
            <span className="text-[10px] text-muted-foreground uppercase">{m.label}</span>
            <span className="text-sm font-semibold tabular-nums">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DetailPanel({ stageId, data }: { stageId: StageId; data: StageDetailData }) {
  return (
    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Mock Header KPIs - could be dynamic based on stage */}
        <Card className="bg-muted/30 border-none shadow-none">
          <CardContent className="p-4 flex flex-col items-center justify-center text-center">
            <span className="text-xs text-muted-foreground uppercase">Total Activos</span>
            <span className="text-2xl font-bold">124</span>
          </CardContent>
        </Card>
        <Card className="bg-muted/30 border-none shadow-none">
          <CardContent className="p-4 flex flex-col items-center justify-center text-center">
            <span className="text-xs text-muted-foreground uppercase">Eficiencia</span>
            <span className="text-2xl font-bold text-green-600">+12%</span>
          </CardContent>
        </Card>
        <Card className="bg-muted/30 border-none shadow-none">
          <CardContent className="p-4 flex flex-col items-center justify-center text-center">
            <span className="text-xs text-muted-foreground uppercase">Costo Promedio</span>
            <span className="text-2xl font-bold">$4.20</span>
          </CardContent>
        </Card>
      </div>

      <Accordion type="single" collapsible defaultValue="group-0" className="w-full">
        {data.groups.map((group, idx) => (
          <AccordionItem key={idx} value={`group-${idx}`} className="border rounded-lg mb-2 px-2">
            <AccordionTrigger className="hover:no-underline px-2">
              <div className="flex flex-col items-start text-left">
                <span className="text-base font-semibold">{group.title}</span>
                <span className="text-xs text-muted-foreground font-normal mt-0.5">
                  {group.summary}
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4 px-2">
              <div className="space-y-1">
                {group.channels.map((channel, cIdx) => (
                  <ChannelRow key={cIdx} channel={channel} />
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      <div className="mt-8 p-4 border border-dashed rounded-lg flex items-center justify-center text-muted-foreground text-sm">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>
            Área de Oportunidad: Configurar{" "}
            {stageId === "ATRACCION" ? "TikTok Ads" : "nuevos canales"}
          </span>
        </div>
      </div>
    </div>
  );
}

// --- MAIN PAGE COMPONENT ---

/**
 *
 */
export default function GrowthDesignPlayground() {
  const [activeStageId, setActiveStageId] = useState<StageId>("ATRACCION");

  const activeDetail = MOCK_DETAILS[activeStageId];

  return (
    <div className="min-h-screen bg-background p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Badge variant="outline" className="border-primary text-primary">
              Design Playground
            </Badge>
            <span className="text-xs text-muted-foreground">v0.1.0 Mock Mode</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Growth Studio Redesign</h1>
          <p className="text-muted-foreground mt-1">
            Iteración rápida de interfaz de usuario con datos simulados.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            Resetear Vista
          </Button>
          <Button size="sm">Guardar Cambios</Button>
        </div>
      </div>

      {/* Stage Selector (Funnel View) */}
      <div className="mb-8 overflow-x-auto pb-4 -mx-4 px-4 scrollbar-hide">
        <div className="flex gap-4 min-w-max">
          {STAGES.map((stage) => (
            <StageCard
              key={stage.id}
              stage={stage}
              isActive={activeStageId === stage.id}
              onClick={() => setActiveStageId(stage.id)}
            />
          ))}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Detail Panel (Left/Center) */}
        <div className="lg:col-span-2">
          <Card className="h-full border-none shadow-sm bg-card/50">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Detalle: {STAGES.find((s) => s.id === activeStageId)?.label}</span>
                <Badge variant="secondary" className="font-normal text-xs">
                  Última actualización: Hace 5 min
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {activeDetail ? (
                <DetailPanel stageId={activeStageId} data={activeDetail} />
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                  <Activity className="w-12 h-12 mb-4 opacity-20" />
                  <p>No hay datos simulados para esta etapa aún.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Action / Context Sidebar (Right) */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm uppercase tracking-wide text-muted-foreground">
                Acciones Rápidas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="secondary" className="w-full justify-start">
                <Target className="w-4 h-4 mr-2" />
                Crear Campaña
              </Button>
              <Button variant="secondary" className="w-full justify-start">
                <Mail className="w-4 h-4 mr-2" />
                Nuevo Email
              </Button>
              <Button variant="secondary" className="w-full justify-start">
                <Users className="w-4 h-4 mr-2" />
                Importar Leads
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-100 dark:border-blue-900">
            <CardContent className="p-4">
              <h4 className="font-semibold text-blue-700 dark:text-blue-300 mb-1 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Insight IA
              </h4>
              <p className="text-sm text-blue-600 dark:text-blue-400">
                La tasa de conversión en{" "}
                <strong>{STAGES.find((s) => s.id === activeStageId)?.label}</strong> ha caído un 5%
                respecto a la semana pasada. Revisa los canales de pago.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
