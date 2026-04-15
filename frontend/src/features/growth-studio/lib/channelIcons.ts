/**
 * Channel Icons Library
 *
 * Maps channel slugs (from backend) to:
 *   - A lucide-react icon component (or inline SVG fallback)
 *   - A brand color hex string for rendering with style={{ color }}
 *
 * Used by ChannelRow and other channel-display components for
 * professional brand recognition instead of emoji placeholders.
 */

import {
  Instagram,
  Facebook,
  Youtube,
  Mail,
  MessageCircle,
  MessageSquare,
  ShoppingCart,
  Search,
  Zap,
  Phone,
  Link,
  BarChart3,
  Radio,
  Target,
  Globe,
  Bot,
} from "lucide-react";

import type { ComponentType, SVGProps } from "react";

export type ChannelIconProps = SVGProps<SVGSVGElement> & {
  className?: string;
};

export type ChannelIconComponent = ComponentType<ChannelIconProps>;

// ─── Icon Mapping ─────────────────────────────────────────────────────────────

/** Exact slug → icon lookup. Populated per channel family. */
const CHANNEL_ICON_MAP: Record<string, ChannelIconComponent> = {
  // Instagram
  instagram: Instagram as ChannelIconComponent,
  "ig-organic": Instagram as ChannelIconComponent,
  "ig-dm": Instagram as ChannelIconComponent,
  // Facebook
  facebook: Facebook as ChannelIconComponent,
  "fb-organic": Facebook as ChannelIconComponent,
  "fb-messenger": Facebook as ChannelIconComponent,
  // YouTube
  youtube: Youtube as ChannelIconComponent,
  "yt-organic": Youtube as ChannelIconComponent,
  "yt-ads": Youtube as ChannelIconComponent,
  // TikTok (no official lucide icon — Radio as fallback)
  tiktok: Radio as ChannelIconComponent,
  "tiktok-organic": Radio as ChannelIconComponent,
  "tiktok-ads": Radio as ChannelIconComponent,
  "tiktok-dm": Radio as ChannelIconComponent,
  "tiktok-retargeting": Radio as ChannelIconComponent,
  // Meta Ads
  "meta-ads": Zap as ChannelIconComponent,
  meta: Zap as ChannelIconComponent,
  "facebook-ads": Zap as ChannelIconComponent,
  "meta-retargeting": Zap as ChannelIconComponent,
  // Google
  "google-ads": Search as ChannelIconComponent,
  "google-search": Search as ChannelIconComponent,
  "ga4-search": Search as ChannelIconComponent,
  "google-organic": Search as ChannelIconComponent,
  "google-retargeting": Search as ChannelIconComponent,
  "search-console": Search as ChannelIconComponent,
  // Shopify / checkout
  shopify: ShoppingCart as ChannelIconComponent,
  "shopify-checkout": ShoppingCart as ChannelIconComponent,
  "checkout-init": ShoppingCart as ChannelIconComponent,
  // MailerLite (email-* prefix handled separately)
  mailerlite: Mail as ChannelIconComponent,
  // WhatsApp
  whatsapp: MessageCircle as ChannelIconComponent,
  "whatsapp-inbound": MessageCircle as ChannelIconComponent,
  "whatsapp-outbound": MessageCircle as ChannelIconComponent,
  // Manychat
  manychat: MessageSquare as ChannelIconComponent,
  "manychat-messenger": MessageSquare as ChannelIconComponent,
  "manychat-ig": MessageSquare as ChannelIconComponent,
  "manychat-wa": MessageSquare as ChannelIconComponent,
  "manychat-sequences": MessageSquare as ChannelIconComponent,
  "manychat-bofu": MessageSquare as ChannelIconComponent,
  "manychat-comments": MessageSquare as ChannelIconComponent,
  // AI SDR / AI agent
  "ai-sdr": Bot as ChannelIconComponent,
  "ai-agent": Bot as ChannelIconComponent,
  "ai-search-organic": Bot as ChannelIconComponent,
  // Outbound / cold contact
  "cold-contact": Phone as ChannelIconComponent,
  outbound: Phone as ChannelIconComponent,
  // Website / landing
  "website-overview": Globe as ChannelIconComponent,
  "website-total": Globe as ChannelIconComponent,
  "meta-pixel": Globe as ChannelIconComponent,
  "website-capture": Globe as ChannelIconComponent,
  "landing-form": Globe as ChannelIconComponent,
  landing: Globe as ChannelIconComponent,
  linkedin: Globe as ChannelIconComponent,
  "linkedin-organic": Globe as ChannelIconComponent,
  // Direct traffic
  direct: Link as ChannelIconComponent,
  // BOFU links
  "meeting-booked": Link as ChannelIconComponent,
  "link-enviado": Link as ChannelIconComponent,
  "checkout-lp": Link as ChannelIconComponent,
  // Abandoned cart
  "abandoned-cart": Target as ChannelIconComponent,
};

/**
 * Returns the appropriate lucide-react icon component for a given channel slug.
 * Falls back to BarChart3 for unknown slugs.
 */
export function getChannelIcon(channelSlug: string): ChannelIconComponent {
  const slug = channelSlug.toLowerCase();
  const icon = CHANNEL_ICON_MAP[slug];
  if (icon) return icon;
  if (slug.startsWith("email-")) return Mail as ChannelIconComponent;
  return BarChart3 as ChannelIconComponent;
}

// ─── Color Mapping ─────────────────────────────────────────────────────────────
// Canonical colors live in @/lib/constants/channel-colors.ts
export { getChannelColor } from "@/lib/constants/channel-colors";
