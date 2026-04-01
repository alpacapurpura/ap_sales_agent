/** @type {import('next').NextConfig} */
const { withSentryConfig } = require("@sentry/nextjs");

// Derive hostnames from environment variables for dev/prod parity
const appDomain = (process.env.NEXT_PUBLIC_APP_URL || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
const apiDomain = (process.env.NEXT_PUBLIC_API_URL || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
const internalApiUrl = process.env.INTERNAL_API_URL;

if (!internalApiUrl) {
  console.warn('⚠️  INTERNAL_API_URL is not set — API rewrites will fail.');
}

// Build allowed origins from env domains
const allowedOrigins = [appDomain, apiDomain].filter(Boolean);
if (process.env.CLERK_DOMAIN) {
  allowedOrigins.push(process.env.CLERK_DOMAIN);
}

// Build image remote patterns from env domains
const imageRemotePatterns = [
  // Prod/dev app and API domains (derived from env)
  ...[appDomain, apiDomain].filter(Boolean).map(hostname => ({
    protocol: 'https',
    hostname,
  })),
  // Placeholder services (always allowed)
  { protocol: 'https', hostname: 'placehold.co' },
  { protocol: 'https', hostname: 'i.pravatar.cc' },
  // Internal Docker hostnames for dev/prod (derived from INTERNAL_API_URL)
  ...(internalApiUrl ? [{
    protocol: 'http',
    hostname: new URL(internalApiUrl).hostname,
  }] : []),
];

const nextConfig = {
  output: 'standalone',
  devIndicators: {
    position: 'bottom-left',
  },
  allowedDevOrigins: allowedOrigins,
  images: {
    remotePatterns: imageRemotePatterns,
  },
  experimental: {
    serverActions: {
      allowedOrigins: allowedOrigins,
    },
  },
  async rewrites() {
    if (!internalApiUrl) return [];
    return [
      {
        source: '/api/webhooks/:path*',
        destination: `${internalApiUrl}/api/v1/webhooks/:path*`,
      },
      {
        source: '/api/v1/:path*',
        destination: `${internalApiUrl}/api/v1/:path*`,
      },
    ]
  },
}

module.exports = withSentryConfig(nextConfig, {
  org: "alpaca-purpura-to",
  project: "nicolify-frontend",
  silent: true,
  hideSourceMaps: true,
  disableLogger: true,
  automaticVercelMonitors: false,
});
