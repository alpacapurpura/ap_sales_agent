# UI Spec: Meta Ads Resumen — Filtro Unificado por Offer

**Fecha:** 2026-04-10
**Alcance:** Refactor de `ResumenTab` + specs de polish por componente
**Feature FSD:** `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/`
**Persona:** Emprendedor/creador, no marketer. Abre Resumen una vez al día, necesita saber en <10s si hoy "está bien" o "hay que hacer algo". Cero tolerancia a números que mienten.

---

## 0. Design Intent

- **Concepto:** "Una pantalla, un foco." El OfferSegmenter es el único control de estado: todo lo demás (KPIs, Inversión, Embudo) obedece. Cambiar de filtro = re-leer el mismo payload, no re-cargar.
- **Emoción objetivo:** Control + confianza. "Sé qué está pasando con mis anuncios y puedo explicar cada número."
- **Principio de confiabilidad:** un número vacío (`—`) con tooltip es superior a un número aproximado sin etiqueta. El `—` nunca es un error — es información.
- **Progressive disclosure:** el valor y el delta se ven de un vistazo; la explicación (qué es, por qué importa, qué hacer) vive en el tooltip, disponible on-demand.

---

## 1. Layout hierarchy (nuevo `ResumenTab`)

### Wireframe ASCII

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [1] Health Check Panel                                             full-width│
│     (sin cambios — ya existe)                                                │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕ 24px
┌──────────────────────────────────────────────────────────────────────────────┐
│ [2] UnassignedBanner   (condicional: solo si unassignedCount > 0)  full-width│
│     ⚠  Tenés N campañas sin asignar · [Asignar ahora]  [×]                  │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕ 24px
┌──────────────────────────────────────────────────────────────────────────────┐
│ [3] OfferSegmenter                                                 full-width│
│     FILTRAR POR OFFER                                                        │
│     ┌──────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ ┌──────────┐   │
│     │Todas │ │🎯 Curso Core│ │💼 Mentoría  │ │⚠ Sin asig. │ │✨ Branding│   │
│     └──────┘ └─────────────┘ └─────────────┘ └────────────┘ └──────────┘   │
│     Contexto activo: "Curso Core · Métrica primaria: Leads · $12.40 CPL"    │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕ 20px
┌──────────────────────────────────────────────────────────────────────────────┐
│ [4] KPI cards (6)                                                  full-width│
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐              │
│  │INVERSIÓN│  ROAS   │ RESULT. │   CPL   │   CTR   │  REACH  │              │
│  │  $1.2k  │  2.4x ? │   47 ?  │ $12.40? │  1.8% ? │   —   ? │              │
│  │ ▲ 12%   │ ▲ 8%    │ ▼ 3%    │ ▼ 5%    │ ▲ 0.2%  │         │              │
│  │ [badge] │         │         │ [badge] │ [badge] │         │              │
│  └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕ 24px
┌──────────────────────────────────────────────────────────────────────────────┐
│ [5] InversionChart                                                 full-width│
│     Inversión y Retorno  ⓘ                                                  │
│     Subtítulo narrativo contextual al filtro                                 │
│     ┌──────────────────────────────────────────────────────────────┐        │
│     │   ▄█ ▄▄ ██                                                    │        │
│     │ ▄██ ██ ██▄ ▄█▄                                                │        │
│     │ ────────────── break-even                                     │        │
│     └──────────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↕ 24px
┌──────────────────────────────────────────────────────────────────────────────┐
│ [6] MetaAdsMiniFunnel                                              full-width│
│     Embudo de Conversión  ⓘ                                                 │
│     Impresiones    12.340  ████████████████████                             │
│                    ↓ 4.2%                                                   │
│     Clics             518  ███                                              │
│                    ↓ 68%                                                    │
│     Landing Views     352  ██                                               │
│                    ↓ 13%                                                    │
│     Leads              47  ▌                                                │
│                    ↓ 12.7%                                                  │
│     Conversiones        6  ▏                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Secciones en orden (tabla)

| # | Sección | Ancho | Condicional | Spacing vs siguiente |
|---|---|---|---|---|
| 1 | `MetaAdsHealthCheckPanel` | full | siempre | 24px (`space-y-6`) |
| 2 | `UnassignedBanner` | full | `hasUnassigned === true` | 24px |
| 3 | `OfferSegmenter` (sticky-candidate) | full | `metricsByOffer.offers.length > 0` | 20px (`space-y-5`) |
| 4 | KPI grid (6 cards) | full | siempre | 24px |
| 5 | `InversionChart` | full | `hasTimeSeries === true` | 24px |
| 6 | `MetaAdsMiniFunnel` | full | siempre (con empty state propio) | — |

- Contenedor raíz: `div.space-y-6` dentro de `TabsContent`. La excepción es que entre el segmentador (3) y los KPIs (4) usamos `space-y-5` visualmente más apretado (ver nota abajo) — se implementa con una clase override o envolviendo 3+4 en un `<section className="space-y-5">`.
- **Razón del espaciado menor 3↔4:** el segmentador y los KPIs son conceptualmente un solo bloque ("filtro + resultado del filtro"). Deben leerse juntos. Las demás secciones son independientes.
- Todas las secciones respetan el contenedor padre del tab: sin márgenes horizontales propios, sin `max-w`.

### Comportamiento sticky (opcional, polish)

- En viewports con scroll largo, el OfferSegmenter puede volverse `sticky top-0 z-10` con un background semi-opaco (`bg-background/95 backdrop-blur`) para que el filtro permanezca visible al hacer scroll hacia el funnel.
- **Decisión:** activarlo solo en `md:` y superiores. En mobile no es necesario y podría chocar con la barra superior del app.

---

## 2. OfferSegmenter spec

### Chips — estados visuales

Todos los chips usan el mismo shell base (radio del `rounded-full`, alto `py-1.5`, padding `px-3`, fuente `text-xs font-medium`, transición 150ms). Lo que cambia por tipo es la paleta.

#### Chip "Todas" — neutral azul

| Estado | Clase / color | Nota |
|---|---|---|
| Default | `border-border bg-card text-muted-foreground` | igual a un chip de offer inactivo |
| Hover | `hover:border-foreground/30 hover:text-foreground` | — |
| Active | `border-blue-500 bg-blue-500/10 text-blue-500` | mismo tratamiento que chip de offer activo |
| Focus visible | `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background` | requerido A11y |

#### Chip de offer (con emoji de arquetipo)

| Estado | Clase / color |
|---|---|
| Default | `border-border bg-card text-muted-foreground` + emoji `text-[13px]` |
| Hover | `hover:border-foreground/30 hover:text-foreground` |
| Active | `border-blue-500 bg-blue-500/10 text-blue-500` + icono `Check` a la izquierda (`h-3 w-3`) reemplaza la holgura del emoji (o se agrega a la derecha del emoji) |
| Disabled | `opacity-50 cursor-not-allowed` (no aplica hoy, reservado) |

**Decisión sobre la marca de activo:** se suma un `Check` mini (`lucide-react`) a la izquierda del emoji cuando está activo. Justificación: borde + background tintado + icon check es 3 señales redundantes — es lo que el usuario necesita para sentir confianza absoluta de qué está filtrado.

#### Chip "Sin asignar" — warning/ámbar (prompt de acción)

| Estado | Clase / color |
|---|---|
| Default | `border-amber-500/40 bg-amber-500/5 text-amber-500` + icono `AlertTriangle h-3 w-3` |
| Hover | `hover:border-amber-500/70 hover:bg-amber-500/10` |
| Active | `border-amber-500 bg-amber-500/15 text-amber-400` + `Check h-3 w-3` |

Razón: el "Sin asignar" no es una offer sino un problema a resolver. Debe diferenciarse tintalmente del resto sin parecer un error bloqueante (rojo). Ámbar = "mirame, hay algo pendiente".

#### Chip "Branding" — neutral con sparkle

| Estado | Clase / color |
|---|---|
| Default | `border-violet-500/30 bg-violet-500/5 text-violet-400` + icono `Sparkles h-3 w-3` |
| Hover | `hover:border-violet-500/60 hover:bg-violet-500/10` |
| Active | `border-violet-500 bg-violet-500/15 text-violet-300` + `Check h-3 w-3` |

Razón: el branding es conceptualmente distinto — no busca conversión directa, busca alcance. Un tono violeta/suave lo marca como "no es un producto, es awareness". El sparkle refuerza la idea de "brillo de marca" sin ser infantil.

### Responsive behavior

| Breakpoint | Comportamiento |
|---|---|
| ≥ `md` (768px) | `flex flex-wrap gap-2` — los chips fluyen en una o dos líneas |
| `sm` (640-767px) | mismo wrap; si hay más de 6 offers, se empieza a permitir 2-3 líneas |
| `< sm` (<640px) | `flex overflow-x-auto gap-2 pb-1 -mx-4 px-4` — scroll horizontal con fade a los costados. NO se convierte en Select para preservar escaneo visual y el valor narrativo de ver emojis/íconos. Se mantiene el `role="group"` |

**Indicador de scroll:** en mobile, un gradiente sutil en el borde derecho (`bg-gradient-to-l from-background`) indica que hay más chips. Ver `references/` del proyecto si existe un patrón — si no, implementar inline.

### Accesibilidad

- Contenedor: `<div role="group" aria-label="Filtrar por offer">` (ya existe).
- Cada chip: `<button type="button" aria-pressed={selected}>` (ya existe).
- **Keyboard nav:** Tab mueve al primer chip, luego Tab entre chips (comportamiento nativo de botones). Flechas `←/→` opcionales — **decisión: no implementar flechas** porque rompe patrón con el resto del dashboard que usa Tab/Enter. Solo focus visible claro.
- **Aria-label por chip:** el label visible es suficiente excepto "Sin asignar" y "Branding", que deben incluir contexto extra:
  - `aria-label="Filtrar por campañas sin asignar a offer"` para Sin asignar
  - `aria-label="Filtrar por campañas de branding (awareness)"` para Branding
- **Live region para el cambio de filtro:** al cambiar el chip activo, se anuncia vía `<div role="status" aria-live="polite" className="sr-only">` con texto: `"Filtro activo: {contextLabel}"`. Implementado como un `<span aria-live="polite" class="sr-only">` dentro del segmentador o a nivel ResumenTab.

### Línea de contexto activo (debajo de los chips)

Cuando un chip de offer está activo, justo debajo del segmentador se muestra una línea de contexto (ya existe parcialmente). Nueva versión:

```
Curso Core · Métrica primaria: Leads · CPL $12.40 · ROAS 2.4x
```

- `text-[11px] text-muted-foreground`
- Nombre de la offer en `font-medium text-foreground`
- Separadores `·` en `text-muted-foreground/60`
- Se omite para "Todas". Para "Branding" muestra: `"Campañas de branding · N activas · Foco: alcance"`. Para "Sin asignar" muestra: `"N campañas sin offer · Asigná cada una para ver métricas por producto"`.

---

## 3. ResumenKpiCard spec — por filtro

### Estructura genérica de una card

```
┌──────────────────────┐
│ LABEL EN MINÚSCULAS ⓘ│  ← label + tooltip trigger (ícono HelpCircle h-3 w-3 al hover del card)
│ $1,234.56            │  ← value (text-xl font-bold tabular-nums)
│ ▲ 12.3% vs ant.      │  ← delta (text-[10px] font-medium)
│ [badge benchmark]    │  ← opcional
└──────────────────────┘
```

- Grid contenedor: `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2.5`
- Card: `rounded-lg border bg-card p-3 space-y-1 relative group` (el `group` habilita mostrar el `?` al hover)
- Label: `text-[10px] text-muted-foreground uppercase tracking-wider flex items-center gap-1`
- Value normal: `text-xl font-bold tabular-nums`
- Value `—`: `text-xl font-bold tabular-nums text-muted-foreground/60`
- Delta positivo: `text-emerald-500` con `TrendingUp h-3 w-3`
- Delta negativo: `text-red-500` con `TrendingDown h-3 w-3`
- Benchmark badge: reusar `BenchmarkBadge` existente

### Tooltip trigger

- Ícono `HelpCircle` de `lucide-react`, `h-3 w-3 text-muted-foreground/50` alineado a la derecha del label.
- **Visibilidad del icono:** siempre visible (`opacity-60`) → en `group-hover` sube a `opacity-100`. No ocultar del todo porque en mobile no hay hover.
- **Hit target:** el `<TooltipTrigger>` de Shadcn debe envolver **el card entero** (no solo el icono), así el usuario con trackpad puede hover el card. Alternativa complementaria: envolver solo el icono para keyboard focus discreto.
- **Implementación:** usar `<Tooltip>` de `@/components/ui/tooltip.tsx` (verificado: existe). `<TooltipProvider delayDuration={200}>` envuelve toda la grid.

### Estado `—` (vacío / no disponible)

- Value: `—` en `text-muted-foreground/60`
- No mostrar delta
- Background: SIN cambio (mismo `bg-card`) — un bg distinto sugeriría error; `—` es información válida
- Un mini ícono `Info h-3 w-3 text-muted-foreground/60` junto al `—` para marcar "hay un porqué, hovereame"
- `aria-label="{label}: no disponible. {unavailableReason}"`

### Acción del filtro "Sin asignar" — card #6

La última card del filtro `unassigned` NO es un KPI. Es una CTA.

- Background: `bg-amber-500/10 border-amber-500/30`
- Label: `ACCIÓN REQUERIDA` en `text-amber-400`
- Body: `"Asigná cada campaña a un offer para ver métricas por producto"` en `text-[11px] text-amber-300/80`
- Botón: `<Button size="sm" variant="outline" className="h-7 border-amber-500/50 text-amber-400 hover:bg-amber-500/20">Asignar ahora</Button>`
- Al hacer click, reusa `handleAssignClick` (misma lógica del banner).

### Sets contextuales por filtro

#### Filtro `all`

| # | Key | Label | Unit | Higher better | Tooltip key | Empty |
|---|---|---|---|---|---|---|
| 1 | `spend` | Inversión | currency | — | `spend` | nunca vacío |
| 2 | `roas` | ROAS | ratio | ✅ | `roas` | si `pixelOff` → `—` |
| 3 | `results` | Resultados | count | ✅ | `results_all` | `0` no es `—` |
| 4 | `cpa` | CPA | currency | ❌ | `cpa` | si `pixelOff` → `—` |
| 5 | `ctr` | CTR | percentage | ✅ | `ctr` | `0%` si sin clicks |
| 6 | `reach_all` | Alcance | count | ✅ | `reach_all` | `—` si `period_metrics` no tiene fila |

#### Filtro `[offerId]`

| # | Key | Label | Unit | Higher better | Tooltip key | Empty |
|---|---|---|---|---|---|---|
| 1 | `spend` | Inversión | currency | — | `spend` | nunca vacío |
| 2 | `roas_or_cost` | ROAS (o "Costo por resultado" si `roas == null`) | ratio / currency | ✅ / ❌ | `roas` / `cost_per_result` | `—` si sin resultados |
| 3 | `results` | `{primaryMetricName}` (Leads/Compras/Mensajes/Calls/Registros/Forms) | count | ✅ | `results_{primaryMetricName}` | `0` es válido |
| 4 | `cpa` | `{CPL|CPA|CPMsg|...}` según `primaryMetricName` | currency | ❌ | `cpl` / `cpa` / etc. | `—` si sin resultados |
| 5 | `ctr` | CTR | percentage | ✅ | `ctr` | — |
| 6 | `reach` | Alcance | count | ✅ | `reach_offer` | `—` si multi-campaña o sin fila |

Mapeo `primaryMetricName` → label de card y key de tooltip:

| primaryMetricName | Label KPI #3 | Label KPI #4 (costo) | Tooltip #3 | Tooltip #4 |
|---|---|---|---|---|
| Leads | Leads | CPL | `results_leads` | `cpl` |
| Compras / Purchases | Compras | CPA | `results_purchases` | `cpa` |
| Mensajes | Mensajes | Costo por mensaje | `results_messages` | `cost_per_message` |
| Calls | Llamadas | Costo por llamada | `results_calls` | `cost_per_call` |
| Registros | Registros | Costo por registro | `results_registrations` | `cost_per_registration` |
| Forms | Forms | Costo por form | `results_forms` | `cost_per_form` |

#### Filtro `branding`

| # | Key | Label | Unit | Higher better | Tooltip key | Empty |
|---|---|---|---|---|---|---|
| 1 | `spend` | Inversión | currency | — | `spend_branding` | — |
| 2 | `reach` | Alcance | count | ✅ | `reach_branding` | `—` si multi-campaña |
| 3 | `impressions` | Impresiones | count | ✅ | `impressions` | — |
| 4 | `cpm` | CPM | currency | ❌ | `cpm` | — |
| 5 | `frequency` | Frecuencia | ratio | neutral | `frequency` | `—` si reach `—` |
| 6 | `target_count` | Campañas activas | count | — | `active_campaigns_branding` | `0` es válido |

#### Filtro `unassigned`

| # | Key | Label | Unit | Higher better | Tooltip key | Empty |
|---|---|---|---|---|---|---|
| 1 | `spend` | Inversión | currency | — | `spend_unassigned` | — |
| 2 | `impressions` | Impresiones | count | — | `impressions` | — |
| 3 | `clicks` | Clics | count | — | `clicks` | — |
| 4 | `ctr` | CTR | percentage | — | `ctr_unassigned` | — |
| 5 | `target_count` | Campañas sin asignar | count | ❌ | `unassigned_campaigns` | — |
| 6 | `action` | **CTA card** (ver arriba) | — | — | — | — |

### Delta display rules

- Delta se muestra solo si `deltaPct != null` (backend lo envía o el hook lo deja null para filtros que no lo soportan aún).
- Formato: `{▲|▼} {abs(deltaPct).toFixed(1)}% vs ant.`
- Color: verde si beneficia, rojo si perjudica, según `higherIsBetter`. Neutro: sin color especial (text-muted-foreground) para métricas sin dirección buena/mala (ej: impresiones en unassigned).
- En la card de `—` no se muestra delta nunca.

### Benchmark badge rules

- Solo se muestra si el backend envía `benchmark` dentro del KPI (existente en `MetricKpiData`).
- Se renderiza con `BenchmarkBadge` (ya existe, reutilizar).
- En el filtro `branding` y `unassigned`, **ocultar badges** — los benchmarks están diseñados para métricas de offer (CPL/CPA), no para segmentos diagnósticos.

---

## 4. Tooltip copy library

> Restricciones: cada `body` ≤ 200 caracteres, tildes obligatorias, tono de "explicame como si no supiera de marketing pero no seas condescendiente".

```typescript
// copy/tooltips.ts
export interface TooltipContent {
  title: string;
  body: string;
}

export const RESUMEN_TOOLTIPS: Record<string, TooltipContent> = {
  // ─────────── Inversión ───────────
  spend: {
    title: "Inversión",
    body: "Lo que gastaste en Meta Ads en el período. Incluye todas las campañas activas. Base de cálculo para ROAS, CPA y CTR.",
  },
  spend_branding: {
    title: "Inversión en Branding",
    body: "Gasto en campañas de awareness (sin objetivo de venta). Invertís para que más gente te conozca, no para cerrar hoy.",
  },
  spend_unassigned: {
    title: "Inversión sin asignar",
    body: "Gasto de campañas que todavía no vinculaste a un producto. Estás pagando, pero no sabés qué offer está generando resultados.",
  },

  // ─────────── ROAS ───────────
  roas: {
    title: "ROAS · Retorno sobre inversión",
    body: "Por cada $1 que gastás, cuánto volvés a facturar. ROAS 2x = recuperás $2 por cada $1. Sano: ≥ 2x. Rojo: < 1x.",
  },

  // ─────────── Resultados (generales y por tipo) ───────────
  results_all: {
    title: "Resultados totales",
    body: "Suma de todos los resultados primarios de tus offers (ventas, leads, mensajes). Es la cosecha real del período.",
  },
  results_leads: {
    title: "Leads",
    body: "Personas que dejaron sus datos (email, WhatsApp) para que los contactes. Siguiente paso: nutrirlos hasta la venta.",
  },
  results_purchases: {
    title: "Compras",
    body: "Ventas directas atribuidas a Meta Ads. Requiere Pixel con evento Purchase configurado en tu checkout.",
  },
  results_messages: {
    title: "Mensajes iniciados",
    body: "Conversaciones nuevas que arrancó Meta Ads (DM, WhatsApp). Cada uno es un prospecto caliente que escribió primero.",
  },
  results_calls: {
    title: "Llamadas",
    body: "Clics en el botón de llamar de tu anuncio. Mide interés alto — si llaman, casi compran.",
  },
  results_registrations: {
    title: "Registros",
    body: "Inscripciones completadas (webinar, curso gratis, evento). Sirven para calificar prospectos antes de vender.",
  },
  results_forms: {
    title: "Forms completados",
    body: "Formularios llenos y enviados. Son leads más calificados que un simple clic porque dedicaron tiempo a completar.",
  },

  // ─────────── Costos por resultado ───────────
  cpa: {
    title: "CPA · Costo por adquisición",
    body: "Cuánto te cuesta cada venta. Más bajo es mejor. Compará contra tu margen: si CPA > ganancia por venta, estás perdiendo.",
  },
  cpl: {
    title: "CPL · Costo por lead",
    body: "Cuánto pagás por cada persona que te dejó sus datos. Sano: entre $1 y $15 según nicho. Más bajo no siempre es mejor si la calidad cae.",
  },
  cost_per_result: {
    title: "Costo por resultado",
    body: "Lo que te cuesta generar un resultado primario de esta offer. Usalo como guía — compará contra tu ticket promedio.",
  },
  cost_per_message: {
    title: "Costo por mensaje",
    body: "Lo que pagás por cada conversación iniciada. Si es bajo pero nadie cierra, el problema no es el anuncio sino tu respuesta.",
  },
  cost_per_call: {
    title: "Costo por llamada",
    body: "Gasto por cada clic en el botón de llamar. Sano si tu ticket es alto; caro si vendés productos de bajo precio.",
  },
  cost_per_registration: {
    title: "Costo por registro",
    body: "Lo que cuesta conseguir una inscripción. Medí la tasa de registro → venta para saber si el registro es barato o caro real.",
  },
  cost_per_form: {
    title: "Costo por form",
    body: "Lo que cuesta un formulario lleno. Suelen ser leads de mejor calidad que un clic simple — justifica un CPA más alto.",
  },

  // ─────────── CTR / CPC / CPM ───────────
  ctr: {
    title: "CTR · Click-through rate",
    body: "% de personas que ven tu anuncio y hacen clic. Bueno: > 1%. Bajo < 0.5% indica que la creativa no engancha — cambiá imagen o copy.",
  },
  ctr_unassigned: {
    title: "CTR (sin asignar)",
    body: "% de clics de campañas que no vinculaste a una offer. Útil para ver si esas campañas están tirando bien antes de asignarlas.",
  },
  cpc: {
    title: "CPC · Costo por clic",
    body: "Lo que pagás por cada clic al anuncio. Depende de nicho y puja. Si sube sin razón, revisá frecuencia y calidad de audiencia.",
  },
  cpm: {
    title: "CPM · Costo por mil impresiones",
    body: "Lo que cuesta mostrar tu anuncio 1.000 veces. Mide precio de la audiencia. CPM alto = audiencia cara (competida o pequeña).",
  },

  // ─────────── Reach / Impresiones / Frecuencia ───────────
  reach_all: {
    title: "Alcance total",
    body: "Personas únicas que vieron al menos un anuncio tuyo. NO es la suma de días ni campañas — es gente, no vistas.",
  },
  reach_offer: {
    title: "Alcance de esta offer",
    body: "Personas únicas alcanzadas por las campañas de esta offer. Disponible cuando hay 1 campaña por offer (sin solape).",
  },
  reach_branding: {
    title: "Alcance de Branding",
    body: "Personas únicas expuestas a tus campañas de awareness. Medí crecimiento mes a mes — es tu cuota de atención.",
  },
  impressions: {
    title: "Impresiones",
    body: "Cantidad de veces que se mostró tu anuncio. Incluye repeticiones a la misma persona (dividí por alcance = frecuencia).",
  },
  clicks: {
    title: "Clics",
    body: "Total de clics en tus anuncios. Incluye clics a link, al perfil o al botón CTA. Dividí por impresiones para sacar CTR.",
  },
  frequency: {
    title: "Frecuencia",
    body: "Cuántas veces en promedio ve tu anuncio cada persona. Sana: 1.5–3. Arriba de 5 aburrís a tu audiencia — rotá la creativa.",
  },

  // ─────────── Campañas activas / sin asignar ───────────
  active_campaigns_branding: {
    title: "Campañas activas",
    body: "Campañas de branding corriendo hoy. Normal: 1 a 3 por vez. Más de 5 y se canibalizan entre sí — consolidá.",
  },
  unassigned_campaigns: {
    title: "Campañas sin asignar",
    body: "Campañas que tenés en Meta pero que no vinculaste a ninguna offer. Asigná cada una para ver métricas por producto.",
  },

  // ─────────── Estados ───────────
  unavailable_generic: {
    title: "Dato no disponible",
    body: "No hay información suficiente para calcular este valor con confianza en este filtro y período.",
  },
  unavailable_reach_overlap: {
    title: "Alcance no combinable",
    body: "El alcance de varias campañas no se puede sumar — las audiencias se solapan. Disponible en 'Todas' o en offers de 1 sola campaña.",
  },
  unavailable_pixel: {
    title: "Requiere Meta Pixel",
    body: "Esta métrica necesita el Meta Pixel instalado en tu sitio, con los eventos configurados (Lead, Purchase, etc.).",
  },
  unavailable_period_pending: {
    title: "Alcance en consolidación",
    body: "El alcance se calcula al cierre de cada día. Volvé mañana para ver el valor definitivo del período.",
  },
  unavailable_no_events: {
    title: "Sin eventos reportados",
    body: "No hubo eventos primarios de esta offer en el período. Verificá que el Pixel esté disparando y que la campaña esté activa.",
  },
  unavailable_metric_not_supported: {
    title: "Métrica no soportada",
    body: "Esta offer no tiene una métrica primaria compatible con Meta Ads. Configurala en Offer Studio para activar el tracking.",
  },

  // ─────────── Funnel steps ───────────
  funnel_impressions: {
    title: "Impresiones",
    body: "Veces que se mostró tu anuncio en el período filtrado. Es la boca del embudo: cuanta más gente lo vea, más oportunidades abajo.",
  },
  funnel_clicks: {
    title: "Clics",
    body: "Personas que hicieron clic después de ver el anuncio. La tasa clics/impresiones es tu CTR.",
  },
  funnel_landing: {
    title: "Vistas de Landing",
    body: "Personas que llegaron a tu página desde el clic. Si hay caída fuerte clics → landing, revisá velocidad y enlace del anuncio.",
  },
  funnel_leads: {
    title: "Leads",
    body: "Prospectos que completaron un formulario o dejaron sus datos. Requiere evento Lead del Pixel en tu landing.",
  },
  funnel_conversions: {
    title: "Conversiones",
    body: "Ventas o resultados finales atribuidos a Meta Ads. Requiere evento Purchase (o el que uses) del Pixel.",
  },
};
```

---

## 5. InversionChart — spec de polish

### Subtítulo narrativo dinámico (contextual al filtro)

El chart ya tiene un subtítulo narrativo. Se extiende para ser contextual al `contextLabel` del hook `useResumenViewData`:

| Filtro | Plantilla |
|---|---|
| `all` | `En los últimos {N} días invertiste {money(totalSpend)} en Meta Ads y generaste {results} resultados — ROAS {roas}x` |
| `offer` | `En {offerName} invertiste {money(totalSpend)} y conseguiste {results} {primaryMetricName} — {roas}x de retorno` |
| `branding` | `Invertiste {money(totalSpend)} en awareness. Esta vista no mide ROAS directo — mirá alcance y frecuencia.` |
| `unassigned` | `Gastaste {money(totalSpend)} en campañas sin asignar. Asigná cada una a un offer para ver su retorno real.` |

- Mismo estilo visual actual (`text-xs`, color dependiente de `narrativeWarn`).
- Cuando `avgRoas < 1` en `all` y `offer`, el subtítulo se tiñe de `text-red-500` y agrega `— por debajo de break-even`.
- En `branding` el subtítulo NUNCA se tiñe de rojo (no hay break-even aplicable).

### Colores break-even (confirmados)

| Elemento | Color | HSL |
|---|---|---|
| Barra rentable (ROAS ≥ 1) | verde | `hsl(142 71% 45%)` |
| Barra bajo break-even (ROAS < 1) | rojo | `hsl(0 84% 60%)` |
| Barra sin ROAS (null) | muted | `hsl(var(--muted))` |
| Línea ROAS | amarillo | `hsl(45 93% 47%)` |
| Línea break-even (y=1) | muted-foreground dashed | — |
| Línea resultados (secundaria) | `chart-2` dashed | `hsl(var(--chart-2))` |

### Tooltip del chart (hover sobre punto)

Campos a mostrar en el tooltip al hacer hover sobre un día:

1. **Fecha larga** — `"10 de abril"` (ya existe)
2. **Inversión** — `formatMoney(spend, tenantCurrency)` (ya existe)
3. **Resultados del día** — `{value} {primaryMetricName plural}` (ej: `"3 Leads"`)
4. **ROAS del día** — `"{roas}x"` o `"—"` si null
5. **NUEVO: Estado** — microchip abajo: `● Rentable` / `● Bajo break-even` / `● Sin pixel` según `getBarColor`

Estructura:
```
┌─────────────────────────┐
│ 10 de abril             │
│ ● Inversión      $45.20 │
│ ● Resultados   3 Leads  │
│ ● ROAS           2.4x   │
│ ─────                   │
│ 🟢 Rentable             │
└─────────────────────────┘
```

### Leyenda

- Posición: abajo del chart (ya existe)
- Items:
  1. Barra verde — "Rentable (ROAS ≥ 1)"
  2. Barra roja — "Bajo break-even"
  3. Línea amarilla — "ROAS"
  4. Línea dashed — "Resultados"
- En filtro `branding`: **ocultar ítem de línea ROAS** (no hay ROAS en branding). El dataset no envía `roas` y la línea no se renderiza.
- `text-[11px] text-muted-foreground`, separación `gap-4`, `flex-wrap`.
- A11y: `role="list"` + cada item `role="listitem"`.

### Empty state

Cuando `compositeData.length === 0`:
```
┌──────────────────────────────────────────┐
│ Inversión y Retorno  ⓘ                  │
│                                          │
│ Sin actividad publicitaria para mostrar  │
│ en este período.                         │
│                                          │
│ [Intentar otro período]                  │
└──────────────────────────────────────────┘
```
- El botón "Intentar otro período" es opcional — solo si el tab tiene control de período. Si no, omitir.

---

## 6. MetaAdsMiniFunnel — spec de polish

### Dimensiones

- Alto de cada paso: `h-6` total (barra `h-1.5` + espacio para etiqueta)
- Ancho de la barra: `100%` del contenedor, el ancho relativo del fill se calcula con `(step.value / maxValue) * 100%` con mínimo 2% para que siempre sea visible si value > 0
- Gap vertical entre pasos: `space-y-3` (antes `space-y-1.5` — se aumenta para que quepa la tasa de conversión visible)
- Padding del container: `p-5` (igual al InversionChart para consistencia)

### Tasa de conversión entre pasos — visible sin hover

Entre cada par de pasos, insertar una línea con la tasa de conversión del paso actual respecto al anterior:

```
Impresiones          12,340     ████████████████████
                     ↓ 4.2%
Clics                   518     ███
                     ↓ 68.0%
Vistas de Landing       352     ██
                     ↓ 13.4%
Leads                    47     ▌
                     ↓ 12.7%
Conversiones              6     ▏
```

- Línea de tasa: `text-[10px]` con ícono `ArrowDown h-3 w-3` alineado a la izquierda
- Color de la tasa: **color ramp** (ver abajo)
- Posición: entre el paso previo y el siguiente, con `-my-1` para que se vea "entre" los pasos visualmente

### Color ramp por tasa de conversión

| Rango | Color texto | Significado |
|---|---|---|
| ≥ 25% (o top 10%) | `text-emerald-500` | excelente |
| 10%–25% | `text-lime-500` | bueno |
| 3%–10% | `text-amber-500` | aceptable |
| 0.5%–3% | `text-orange-500` | bajo |
| < 0.5% | `text-red-500` | problemático |
| `null` (primer paso) | (se omite la línea) | — |

**Nota importante:** los rangos saludables dependen del tipo de métrica (CTR es típicamente 1-3%, tasa landing→lead es 10-30%). Para simplificar V1, usamos la tabla anterior como aproximación universal. Documentado como deuda técnica en `to-do.md` para V2.

### Barras de ancho

- Color base: `bg-blue-500` para el primer paso, `bg-blue-500/70` para los demás (ya existe)
- **Mejora:** aplicar el mismo color ramp que la tasa a la barra del paso receptor, así el color es consistente ("este paso está rojo → mirá la tasa de arriba").
- Fallback: si `conversionRate == null`, usar el color neutro azul.

### Empty state (todos los valores = 0)

Detectado por: `steps.every(s => s.value === 0)`

```
┌──────────────────────────────────────────┐
│ Embudo de Conversión  ⓘ                 │
│                                          │
│        📭                                │
│   Sin actividad medible en este          │
│   período y filtro.                      │
│                                          │
│   [Ver cómo configurar el Pixel →]       │
│                                          │
└──────────────────────────────────────────┘
```
- Icono `Inbox` o `BarChart3` en `h-8 w-8 text-muted-foreground/40`
- Texto: `text-sm text-muted-foreground`
- CTA: link a docs del pixel, `text-xs text-blue-500 hover:underline`
- El mensaje varía según filtro:
  - `all`: "Sin actividad medible en este período"
  - `offer`: "Esta offer aún no tiene campañas asignadas o no reportó eventos"
  - `branding`: "Sin impresiones de branding en este período"
  - `unassigned`: "Las campañas sin asignar no reportaron eventos"

### Paso con `value === 0` pero otros pasos con datos

- Renderizar el paso con barra en width 2% (mínimo visible)
- Tasa de conversión con ese paso: `0.0%` coloreado en rojo
- NO mostrar `—` (porque 0 es un dato real, no "desconocido")

### Paso con `value === null` (dato no disponible)

- Value se muestra como `—` con tooltip `unavailable_pixel` o `unavailable_generic`
- Barra: `bg-muted` (sin fill azul)
- Tasa de conversión con ese paso: también `—` y se oculta la línea de tasa

### Tooltip por paso

- Ícono `HelpCircle h-3 w-3` al lado del label del paso (solo visible en hover del contenedor del paso, `group`)
- Contenido: usa `funnel_impressions`, `funnel_clicks`, `funnel_landing`, `funnel_leads`, `funnel_conversions` de `RESUMEN_TOOLTIPS`

### Accesibilidad

- Contenedor: `<div role="list" aria-label="Embudo de conversión">`
- Cada paso: `<div role="listitem" aria-label="{step.label}: {value}, tasa desde paso anterior {conversionRate}%">`
- Tasa como texto narrativo, no solo color

---

## 7. KPI Cards polish spec

### Tipografía

| Elemento | Clase Tailwind | Rationale |
|---|---|---|
| Label | `text-[10px] font-semibold text-muted-foreground uppercase tracking-wider` | compacto, jerárquicamente bajo |
| Value (normal) | `text-xl font-bold tabular-nums text-foreground leading-none` | dominante, `leading-none` para que no empuje el delta |
| Value (`—`) | `text-xl font-bold tabular-nums text-muted-foreground/60 leading-none` | atenuado pero igual de grande |
| Delta | `text-[10px] font-medium` + color semántico | pequeño, secundario |
| Benchmark badge | heredado de `BenchmarkBadge` | — |

### Spacing

- Padding del card: `p-3` (igual al actual)
- Gap interno entre label / value / delta: `space-y-1` (ya existe)
- Gap entre cards: `gap-2.5` (ya existe)
- Min-height del card: **NUEVO** — `min-h-[92px]` para que cards con delta y cards sin delta queden alineadas en altura

### Color semántico del delta

| `higherIsBetter` | Signo delta | Color texto | Ícono |
|---|---|---|---|
| `true` | positivo | `text-emerald-500` | `TrendingUp` |
| `true` | negativo | `text-red-500` | `TrendingDown` |
| `false` | positivo | `text-red-500` | `TrendingUp` |
| `false` | negativo | `text-emerald-500` | `TrendingDown` |
| `undefined` (neutro) | cualquiera | `text-muted-foreground` | flecha respectiva |

Formato: `{icon} {abs(delta).toFixed(1)}% vs ant.`

### Tooltip trigger — decisión final

- **Componente Shadcn:** `@/components/ui/tooltip.tsx` (verificado: existe).
- **Wrapper:** todo el card es `<TooltipTrigger asChild>` envolviendo un `<div>` clickable (no-op click). Esto da el hover en toda el área del card sin mover el label.
- **Icono visual:** un `HelpCircle h-3 w-3` al lado del label (opacity `60% → 100% en hover`) confirma al usuario que hay info disponible. El icono NO es el hit-target, es solo pista visual.
- **Delay:** `<TooltipProvider delayDuration={250}>` a nivel grid.
- **Side:** `side="top"` por defecto; la fila inferior de un grid puede usar `side="bottom"`. Shadcn lo detecta automáticamente con `collisionPadding`.
- **Max width:** `max-w-xs` para que los textos de 200 caracteres queden legibles en ~3 líneas.

### Aria-label por card

```tsx
<div
  role="group"
  aria-label={`${label}: ${ariaValue}${deltaPct != null ? `, variación ${deltaPct}% respecto al período anterior` : ''}. ${tooltip.body}`}
>
```

- `ariaValue`:
  - Si value es `—`: `"no disponible"`
  - Si unit es currency: `"${amount} ${currency}"`
  - Si unit es percentage: `"${value} por ciento"`
  - Si unit es ratio: `"${value} veces"`
  - Si unit es count: `"${value.toLocaleString('es')}"`

### Estado pixel-off (valor es 0 por falta de Pixel)

- Reemplazar value por `—` (mismo tratamiento que "no disponible")
- `unavailableReason = "unavailable_pixel"`
- El tooltip cambia al de `unavailable_pixel` además del KPI base
- Se mantiene el delta oculto (no tiene sentido mostrar 0% vs 0%)

---

## 8. Estados globales

### Loading

- **NO** spinner global que bloquee la tab.
- Cada sección tiene su propio skeleton, usando `<Skeleton>` de `@/components/ui/skeleton.tsx`:

| Sección | Skeleton |
|---|---|
| Health Check | Ya existe — 1 card con 3 líneas placeholder |
| Unassigned Banner | No aplica (solo se muestra con datos) |
| OfferSegmenter | 4 chips skeleton (`h-7 w-20 rounded-full`) |
| KPI Cards (6) | `<Skeleton className="h-[92px] rounded-lg" />` × 6 dentro del grid |
| InversionChart | 1 card con `<Skeleton className="h-[320px] rounded-lg" />` + 3 líneas de subtítulo (`h-3 w-2/3`) |
| MetaAdsMiniFunnel | 5 filas con label + barra skeleton (`h-1.5 w-full`) |

- El `ResumenTab` recibe `isLoading`. Cuando `isLoading === true`, renderiza los skeletons de arriba en lugar del contenido. Nunca muestra mitad-contenido mitad-skeleton (para evitar flash).

### Empty (sin datos para el período)

- Mensaje uniforme: "No hay datos de Meta Ads para este período"
- Componente: un `<EmptyState>` ligero inline por sección, NO un take-over de toda la tab
- Icono: `BarChart3` o `Inbox` en `h-8 w-8 text-muted-foreground/40`
- En cada sección (InversionChart y MetaAdsMiniFunnel) ya definimos empty states específicos en Secciones 5 y 6
- KPI cards en empty: todas con value `—` y tooltip de "no data en período"

### Error

- Error en `useMetricsByOffer` o `useMetaHealthCheck` → `<Alert variant="destructive">` por sección afectada, con botón "Reintentar" que llama al refetch.
- **NO** bloquear las otras secciones si solo una falla — cada sección envuelta en su propio `ErrorBoundary` (`features/growth-studio/components/metrics-dashboard/shared/SectionErrorBoundary.tsx` si existe, si no, crear uno simple).
- Mensaje genérico: "No pudimos cargar {sección}. Intentá de nuevo en unos segundos."

---

## 9. Accesibilidad (WCAG AA)

### Contraste mínimo

- Todos los colores de texto sobre `bg-card` deben pasar AA (4.5:1 para texto normal, 3:1 para UI components y texto grande).
- **Verificar manualmente:**
  - `text-muted-foreground/60` (usado en `—`): puede estar en el límite. Fallback: `text-muted-foreground` sin opacidad.
  - `text-amber-500` sobre `bg-amber-500/10`: puede fallar en light mode. Ya validado en `UnassignedBanner`.
  - Delta `text-emerald-500` y `text-red-500`: OK en dark mode (ver `globals.css`), verificar en light.

### Keyboard navigation

**Orden de Tab stops dentro de `ResumenTab`:**
1. Botones del Health Check (existente)
2. Botón "Asignar ahora" del UnassignedBanner (existente)
3. Botón `×` dismiss del UnassignedBanner (existente)
4. Chip "Todas" del OfferSegmenter
5. Chip offer #1, #2, #3... (en orden)
6. Chip "Sin asignar"
7. Chip "Branding"
8. (KPIs no son Tab stops — son grupos con role=group; se leen con screen reader pero no reciben foco por Tab)
9. Chart de Inversión: el `<ChartContainer>` no es focusable por defecto; Recharts maneja foco interno en tooltips
10. Funnel: no-focusable (es solo display)

- **Enter / Space** sobre un chip dispara `onSelect`.
- **Focus visible:** todos los botones deben tener `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`.
- **Escape:** no aplica (no hay modales abiertos).

### Screen reader — cambios de filtro

- Al cambiar el chip activo, anunciar vía live region:
  ```tsx
  <span role="status" aria-live="polite" className="sr-only">
    {`Filtro activo: ${contextLabel}. Mostrando ${kpis.length} métricas.`}
  </span>
  ```
- Ubicación: dentro del `ResumenTab`, como primer hijo no-visible.
- Actualización: cada vez que `selectedOfferId` cambia, se actualiza el texto del span y el screen reader anuncia el cambio.

### Tooltips

- Shadcn `Tooltip` ya implementa el patrón correcto (`role="tooltip"`, `aria-describedby` en el trigger).
- **Requisito extra:** el tooltip debe ser alcanzable con keyboard (Focus sobre el card → tooltip aparece automáticamente). Shadcn lo hace si el trigger es un elemento focusable. Como nuestro card wrapper es un `<div>`, debemos pasarlo a un `<button>` o dar `tabIndex={0}` para que sea focusable.
- **Decisión:** KPI card = `<div tabIndex={0} role="group">`. No es un botón (no hay acción al click), pero sí debe ser keyboard-reachable.

---

## 10. Component Tree & FSD

```
ResumenTab (Client — "use client")
├── MetaAdsHealthCheckPanel (existing, no changes)
├── UnassignedBanner (existing, no changes)
├── OfferSegmenter (existing, polish — see §2)
│   ├── Chip "Todas"
│   ├── Chip offer × N
│   ├── Chip "Sin asignar" (conditional)
│   └── Chip "Branding" (conditional)
├── ContextLabelLine (new — inline, no file)
├── ResumenKpiGrid (new component file)
│   └── ResumenKpiCard × 6 (new component file)
│       ├── Label + HelpCircle
│       ├── Value / "—"
│       ├── Delta (optional)
│       ├── BenchmarkBadge (optional, existing)
│       └── Shadcn Tooltip wrapper
├── InversionChart (existing, polish — see §5)
└── MetaAdsMiniFunnel (existing, polish — see §6)
```

### Archivos nuevos / modificados

```
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/
├── tabs/
│   └── ResumenTab.tsx                          # MODIFIED — nuevo layout, usa hook
├── hooks/
│   └── useResumenViewData.ts                   # NEW — hook unificado (spec en CONTRACT.md)
├── copy/
│   └── tooltips.ts                             # NEW — RESUMEN_TOOLTIPS (§4)
├── OfferSegmenter.tsx                           # MODIFIED — chips tintados, Check icon
├── ResumenKpiGrid.tsx                           # NEW — grid wrapper
├── ResumenKpiCard.tsx                           # NEW — card individual con tooltip
├── ResumenContextLabel.tsx                      # NEW — línea de contexto bajo segmenter
├── MetaAdsMiniFunnel.tsx                        # MODIFIED — tasa visible, color ramp, empty
├── InversionChart.tsx                           # MODIFIED — subtítulo contextual, tooltip rico
└── __tests__/
    ├── ResumenTab.test.tsx                      # MODIFIED — cambios de filtro afectan KPIs+chart+funnel
    ├── ResumenKpiCard.test.tsx                  # NEW — estados (valor, `—`, delta, tooltip)
    ├── OfferSegmenter.test.tsx                  # MODIFIED — verifica tint por tipo de chip
    └── MetaAdsMiniFunnel.test.tsx               # NEW — tasa entre pasos, color ramp, empty
```

---

## 11. Shadcn Components Used

| Componente | Ruta | Uso |
|---|---|---|
| `Tooltip`, `TooltipProvider`, `TooltipTrigger`, `TooltipContent` | `@/components/ui/tooltip` | Todos los tooltips de KPI cards y funnel steps |
| `Button` | `@/components/ui/button` | CTA "Asignar ahora" en banner y card de unassigned |
| `Skeleton` | `@/components/ui/skeleton` | Loading states por sección |
| `Alert`, `AlertDescription` | `@/components/ui/alert` | Error states por sección |
| `Badge` (si hace falta tag visual) | `@/components/ui/badge` | Reservado para benchmarks; actualmente se usa `BenchmarkBadge` propio |
| `Separator` | `@/components/ui/separator` | Opcional, entre secciones si se quiere divisor (decisión: NO usar, el espacio es suficiente) |

**No usar:** `Card` component shadcn — el proyecto usa `<div className="rounded-lg border bg-card">` consistentemente. Mantener ese patrón.

---

## 12. Interaction Patterns

| Trigger | Efecto | Feedback visual | A11y announce |
|---|---|---|---|
| Click chip OfferSegmenter | `onSelect(id)` → hook recalcula `ResumenViewData` | Chip se tinta activo; todos los KPIs, chart y funnel se re-renderizan | "Filtro activo: {contextLabel}" |
| Hover sobre KPI card | `<HelpCircle>` sube a opacity 100; Shadcn Tooltip aparece después de 250ms | Tooltip con title + body | `aria-describedby` del tooltip |
| Focus sobre KPI card (keyboard) | mismo que hover | mismo | mismo |
| Hover sobre barra del InversionChart | Tooltip del chart aparece | Tooltip rico con fecha, inversión, resultados, ROAS, estado | — |
| Hover sobre paso del funnel | Tooltip aparece | Tooltip con title + body del step | `aria-describedby` |
| Click "Asignar ahora" (banner o card CTA) | `handleAssignClick` → navega a tab "Campañas" o abre drawer | — | — |
| Período cambia (externo al tab) | `useMetricsByOffer(period)` re-fetches | Skeletons de KPIs/chart/funnel mientras carga | — |

---

## 13. Responsive Behavior

| Breakpoint | KPI grid | OfferSegmenter | Chart | Funnel |
|---|---|---|---|---|
| `< sm` (<640px) | `grid-cols-2` | `overflow-x-auto` con scroll horizontal | `h-[240px]` | filas compactas, label truncado si >18 chars |
| `sm` (640-767px) | `grid-cols-3` | `flex flex-wrap` | `h-[280px]` | normal |
| `md` (768-1023px) | `grid-cols-3` | `flex flex-wrap` | `h-[320px]` | normal |
| `lg` (≥1024px) | `grid-cols-6` | `flex flex-wrap` | `h-[320px]` | normal |

- En `< sm`, la línea de contexto bajo el segmenter se colapsa a dos líneas si hace falta.
- En `< sm`, el InversionChart puede ocultar la línea de resultados (dashed) si el chart se ve sobrecargado — decisión del especialista de polish de chart.

---

## 14. Design Principles (resumen)

1. **"Un número con `—` es más honesto que un número aproximado sin etiqueta."** Confiabilidad > completitud.
2. **"El filtro es el estado, todo lo demás es derivación."** Cambiar de offer NO re-fetchea; muta la vista derivada de un único payload.
3. **"Cada número tiene un tooltip."** Si el usuario no sabe qué es CPL, el producto debe enseñarle sin sacarlo del flujo.
4. **"El `—` es un feature."** Tiene ícono propio, tooltip dedicado y color atenuado. No es un bug ni un skeleton.
5. **"El branding y el unassigned son ciudadanos de segunda categoría — a propósito."** Son diagnósticos, no protagonistas. Color tintado, contador de campañas en lugar de ROAS, CTAs suaves.

---

## 15. Open questions (para architect / backend agents)

1. `period_metrics` — ¿almacena reach a nivel campaña para `meta-ads`? Si no, el reach por offer de 1 campaña también será `—` hasta que el ETL se actualice (ya anotado en el spec).
2. ¿`deltaPct` se computa en backend para todos los filtros o solo para `all`? Si solo para `all`, el hook del frontend debe pasar `null` y las cards no mostrarán delta para `offer/branding/unassigned` hasta que el backend lo implemente.
3. ¿Existe un `SectionErrorBoundary` en `shared/`? Si no, se crea uno mínimo como parte de este refactor.

---

**Fin del UI-SPEC.**
