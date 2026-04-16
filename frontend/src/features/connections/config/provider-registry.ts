import { type ComponentType, lazy } from "react";

export interface ProviderDefinition {
  id: string;
  name: string;
  description: string;
  icon: string; // For BrandIcon component
  tags: string[];
  status: "available" | "coming_soon";
  /** Lazy-loaded component for the detail/config view */
  component: ComponentType;
}

// Lazy-load each connection view to keep the hub bundle small
const MetaView = lazy(() =>
  import("@/features/connections/components/MetaView").then((m) => ({ default: m.MetaView })),
);
const ShopifyView = lazy(() =>
  import("@/features/connections/components/ShopifyView").then((m) => ({
    default: m.ShopifyView,
  })),
);
const WhatsAppView = lazy(() => import("@/features/connections/components/WhatsappView").then((m) => ({ default: m.WhatsAppView })));
const GoogleWorkspaceView = lazy(() =>
  import("@/features/connections/components/GoogleWorkspaceView").then((m) => ({
    default: m.GoogleWorkspaceView,
  })),
);
const GoogleAnalyticsView = lazy(() =>
  import("@/features/connections/components/GoogleAnalyticsView").then((m) => ({
    default: m.GoogleAnalyticsView,
  })),
);
const YouTubeView = lazy(() =>
  import("@/features/connections/components/YoutubeView").then((m) => ({
    default: m.YoutubeView,
  })),
);
const TelegramView = lazy(() =>
  import("@/features/connections/components/TelegramView").then((m) => ({
    default: m.TelegramView,
  })),
);
const ManyChatView = lazy(() =>
  import("@/features/connections/components/ManychatView").then((m) => ({
    default: m.ManyChatView,
  })),
);
const MailerLiteView = lazy(() =>
  import("@/features/connections/components/MailerliteView").then((m) => ({
    default: m.MailerLiteView,
  })),
);
const GmailView = lazy(() =>
  import("@/features/connections/components/GmailView").then((m) => ({
    default: m.GmailView,
  })),
);
const GoogleCalendarView = lazy(() =>
  import("@/features/connections/components/GoogleCalendarView").then((m) => ({
    default: m.GoogleCalendarView,
  })),
);

/**
 * Provider Registry — single source of truth for all integrations.
 *
 * Tags are flexible (no rigid categories). The hub uses them for filter chips.
 * Order matters: connected-first sorting happens at runtime, but this controls
 * the default display order for unconnected providers.
 */
export const PROVIDER_REGISTRY: ProviderDefinition[] = [
  {
    id: "meta",
    name: "Meta Business Suite",
    description: "Facebook, Instagram, Ads y Pixel",
    icon: "meta",
    tags: ["social", "analytics", "ads"],
    status: "available",
    component: MetaView,
  },
  {
    id: "shopify",
    name: "Shopify",
    description: "Tienda online, pedidos y analytics",
    icon: "shopify",
    tags: ["e-commerce"],
    status: "available",
    component: ShopifyView,
  },
  {
    id: "whatsapp",
    name: "WhatsApp",
    description: "Mensajería directa con clientes",
    icon: "whatsapp",
    tags: ["mensajería"],
    status: "available",
    component: WhatsAppView,
  },
  {
    id: "google-workspace",
    name: "Google Workspace",
    description: "Gmail, Calendar y servicios de Google",
    icon: "google",
    tags: ["email", "calendario"],
    status: "available",
    component: GoogleWorkspaceView,
  },
  {
    id: "google-analytics",
    name: "Google Analytics",
    description: "Métricas web y conversión",
    icon: "ga4",
    tags: ["analytics"],
    status: "available",
    component: GoogleAnalyticsView,
  },
  {
    id: "youtube",
    name: "YouTube",
    description: "Videos, canal y analytics",
    icon: "youtube",
    tags: ["social", "analytics"],
    status: "available",
    component: YouTubeView,
  },
  {
    id: "manychat",
    name: "ManyChat",
    description: "Chatbots y automatización de mensajes",
    icon: "manychat",
    tags: ["mensajería", "automatización"],
    status: "available",
    component: ManyChatView,
  },
  {
    id: "telegram",
    name: "Telegram",
    description: "Bot de mensajería y notificaciones",
    icon: "telegram",
    tags: ["mensajería"],
    status: "available",
    component: TelegramView,
  },
  {
    id: "mailerlite",
    name: "MailerLite",
    description: "Email marketing y newsletters",
    icon: "mailerlite",
    tags: ["email", "marketing"],
    status: "available",
    component: MailerLiteView,
  },
  {
    id: "gmail",
    name: "Gmail",
    description: "Envío de correos transaccionales",
    icon: "google",
    tags: ["email"],
    status: "available",
    component: GmailView,
  },
  {
    id: "google-calendar",
    name: "Google Calendar",
    description: "Agenda y reuniones",
    icon: "google",
    tags: ["calendario"],
    status: "available",
    component: GoogleCalendarView,
  },
  {
    id: "tiktok",
    name: "TikTok",
    description: "Videos cortos y ads",
    icon: "tiktok",
    tags: ["social", "ads"],
    status: "coming_soon",
    component: lazy(() => Promise.resolve({ default: () => null })),
  },
  {
    id: "webwidget",
    name: "Web Widget",
    description: "Chat widget para tu sitio web",
    icon: "widget",
    tags: ["mensajería"],
    status: "coming_soon",
    component: lazy(() => Promise.resolve({ default: () => null })),
  },
];

/** Lookup provider by id */
export function getProvider(id: string): ProviderDefinition | undefined {
  return PROVIDER_REGISTRY.find((p) => p.id === id);
}

/** Get unique tags from all providers, sorted alphabetically */
export function getAllTags(): string[] {
  const tags = new Set<string>();
  for (const p of PROVIDER_REGISTRY) {
    for (const t of p.tags) tags.add(t);
  }
  return Array.from(tags).sort();
}

/**
 * Maps provider registry IDs to the ChannelType values used in the backend.
 * The batch status endpoint returns channel_type values; this maps them back.
 */
export const PROVIDER_TO_CHANNEL_TYPES: Record<string, string[]> = {
  meta: ["meta"],
  shopify: ["shopify"],
  whatsapp: ["whatsapp", "whatsapp_cloud"],
  "google-workspace": ["google_calendar", "gmail"],
  "google-analytics": ["google_analytics"],
  youtube: ["youtube", "youtube_analytics"],
  manychat: ["manychat"],
  telegram: ["telegram"],
  mailerlite: ["mailerlite"],
  gmail: ["gmail"],
  "google-calendar": ["google_calendar"],
  tiktok: [],
  webwidget: [],
};
