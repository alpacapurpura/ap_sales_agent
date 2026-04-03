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

import type { ComponentType, SVGProps } from 'react';
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
} from 'lucide-react';

export type ChannelIconProps = SVGProps<SVGSVGElement> & {
  className?: string;
};

export type ChannelIconComponent = ComponentType<ChannelIconProps>;

// ─── Icon Mapping ─────────────────────────────────────────────────────────────

/**
 * Returns the appropriate lucide-react icon component for a given channel slug.
 * Falls back to BarChart3 for unknown slugs.
 */
export function getChannelIcon(channelSlug: string): ChannelIconComponent {
  const slug = channelSlug.toLowerCase();

  // Instagram (organic + DM)
  if (slug === 'instagram' || slug === 'ig-organic' || slug === 'ig-dm') {
    return Instagram as ChannelIconComponent;
  }

  // Facebook (organic + messenger)
  if (slug === 'facebook' || slug === 'fb-organic' || slug === 'fb-messenger') {
    return Facebook as ChannelIconComponent;
  }

  // YouTube (organic + ads)
  if (slug === 'youtube' || slug === 'yt-organic' || slug === 'yt-ads') {
    return Youtube as ChannelIconComponent;
  }

  // TikTok (organic + ads + DM) — no official TikTok icon in lucide; use Radio as fallback
  if (slug === 'tiktok' || slug === 'tiktok-organic' || slug === 'tiktok-ads' || slug === 'tiktok-dm' || slug === 'tiktok-retargeting') {
    return Radio as ChannelIconComponent;
  }

  // Meta Ads / Meta retargeting
  if (slug === 'meta-ads' || slug === 'meta' || slug === 'facebook-ads' || slug === 'meta-retargeting') {
    return Zap as ChannelIconComponent;
  }

  // Google (ads, search, GA4, retargeting, Search Console)
  if (
    slug === 'google-ads' ||
    slug === 'google-search' ||
    slug === 'ga4-search' ||
    slug === 'google-organic' ||
    slug === 'google-retargeting' ||
    slug === 'search-console'
  ) {
    return Search as ChannelIconComponent;
  }

  // Shopify / checkout
  if (slug === 'shopify' || slug === 'shopify-checkout' || slug === 'checkout-init') {
    return ShoppingCart as ChannelIconComponent;
  }

  // Email marketing (provider-agnostic email-* slugs + legacy mailerlite)
  if (slug.startsWith('email-') || slug === 'mailerlite') {
    return Mail as ChannelIconComponent;
  }

  // WhatsApp
  if (slug === 'whatsapp' || slug === 'whatsapp-inbound' || slug === 'whatsapp-outbound') {
    return MessageCircle as ChannelIconComponent;
  }

  // Manychat / Facebook Messenger bot + IG, WA, sequences, BOFU, comments
  if (
    slug === 'manychat' ||
    slug === 'manychat-messenger' ||
    slug === 'manychat-ig' ||
    slug === 'manychat-wa' ||
    slug === 'manychat-sequences' ||
    slug === 'manychat-bofu' ||
    slug === 'manychat-comments'
  ) {
    return MessageSquare as ChannelIconComponent;
  }

  // AI SDR / AI agent channels
  if (slug === 'ai-sdr' || slug === 'ai-agent' || slug === 'ai-search-organic') {
    return Bot as ChannelIconComponent;
  }

  // Cold contact / outbound
  if (slug === 'cold-contact' || slug === 'outbound') {
    return Phone as ChannelIconComponent;
  }

  // Website overview
  if (slug === 'website-overview' || slug === 'website-total' || slug === 'meta-pixel' || slug === 'website-capture') {
    return Globe as ChannelIconComponent;
  }

  // Landing form / web forms
  if (slug === 'landing-form' || slug === 'landing') {
    return Globe as ChannelIconComponent;
  }

  // Direct traffic
  if (slug === 'direct') {
    return Link as ChannelIconComponent;
  }

  // Abandoned cart
  if (slug === 'abandoned-cart') {
    return Target as ChannelIconComponent;
  }

  // Meeting / payment link
  if (slug === 'meeting-booked' || slug === 'link-enviado' || slug === 'checkout-lp') {
    return Link as ChannelIconComponent;
  }

  // LinkedIn
  if (slug === 'linkedin' || slug === 'linkedin-organic') {
    return Globe as ChannelIconComponent;
  }

  // Default fallback
  return BarChart3 as ChannelIconComponent;
}

// ─── Color Mapping ─────────────────────────────────────────────────────────────

/**
 * Returns the brand hex color for a given channel slug.
 * Falls back to a neutral muted-foreground HSL value for unknown slugs.
 */
export function getChannelColor(channelSlug: string): string {
  const slug = channelSlug.toLowerCase();

  // Instagram — gradient purple/pink; use solid purple
  if (slug === 'instagram' || slug === 'ig-organic' || slug === 'ig-dm') {
    return '#E4405F';
  }

  // Facebook — blue
  if (slug === 'facebook' || slug === 'fb-organic' || slug === 'fb-messenger') {
    return '#1877F2';
  }

  // YouTube — red
  if (slug === 'youtube' || slug === 'yt-organic' || slug === 'yt-ads') {
    return '#FF0000';
  }

  // TikTok — black (use dark gray for visibility on light backgrounds)
  if (slug === 'tiktok' || slug === 'tiktok-organic' || slug === 'tiktok-ads' || slug === 'tiktok-dm' || slug === 'tiktok-retargeting') {
    return '#010101';
  }

  // Meta Ads — Meta blue
  if (slug === 'meta-ads' || slug === 'meta' || slug === 'facebook-ads' || slug === 'meta-retargeting') {
    return '#0082FB';
  }

  // Google — Google blue (primary)
  if (
    slug === 'google-ads' ||
    slug === 'google-search' ||
    slug === 'ga4-search' ||
    slug === 'google-organic' ||
    slug === 'google-retargeting' ||
    slug === 'search-console'
  ) {
    return '#4285F4';
  }

  // Shopify — green
  if (slug === 'shopify' || slug === 'shopify-checkout' || slug === 'checkout-init') {
    return '#96BF48';
  }

  // Email marketing — orange (provider-agnostic email-* slugs + legacy mailerlite)
  if (slug.startsWith('email-') || slug === 'mailerlite') {
    return '#F6921E';
  }

  // WhatsApp — green
  if (slug === 'whatsapp' || slug === 'whatsapp-inbound' || slug === 'whatsapp-outbound') {
    return '#25D366';
  }

  // Manychat — purple
  if (
    slug === 'manychat' ||
    slug === 'manychat-messenger' ||
    slug === 'manychat-ig' ||
    slug === 'manychat-wa' ||
    slug === 'manychat-sequences' ||
    slug === 'manychat-bofu' ||
    slug === 'manychat-comments'
  ) {
    return '#7B3FE4';
  }

  // AI SDR — neutral blue
  if (slug === 'ai-sdr' || slug === 'ai-agent' || slug === 'ai-search-organic') {
    return '#6366F1';
  }

  // Website — blue
  if (slug === 'website-overview' || slug === 'website-total' || slug === 'meta-pixel' || slug === 'website-capture') {
    return '#3B82F6';
  }

  // LinkedIn — LinkedIn blue
  if (slug === 'linkedin' || slug === 'linkedin-organic') {
    return '#0A66C2';
  }

  // Fallback — muted foreground equivalent
  return 'hsl(215.4 16.3% 46.9%)';
}
