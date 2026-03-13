/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  devIndicators: {
    buildActivity: true,
    buildActivityPosition: 'bottom-left',
  },
  // Whitelist local domains for development to prevent "Cross origin request detected" errors
  allowedDevOrigins: ["dev-app.nicolify.com", "dev-api.nicolify.com"],
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'app.nicolify.com',
      },
      {
        protocol: 'https',
        hostname: 'api.nicolify.com', // Production API
      },
      {
        protocol: 'https',
        hostname: 'dev-app.nicolify.com',
      },
      {
        protocol: 'https',
        hostname: 'dev-api.nicolify.com',
      },
      {
        protocol: 'https',
        hostname: 'placehold.co',
      },
      {
        protocol: 'https',
        hostname: 'i.pravatar.cc',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
      },
      {
        protocol: 'http',
        hostname: 'visionarias_brain_dev',
      },
      {
        protocol: 'http',
        hostname: 'backend',
      }
    ],
  },
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000', 'clerk.nicolify.com', 'dev-app.nicolify.com', 'dev-api.nicolify.com', 'app.nicolify.com', 'api.nicolify.com']
    }
  },
  async rewrites() {
    return [
      {
        source: '/api/webhooks/:path*',
        destination: `${process.env.INTERNAL_API_URL || 'http://visionarias_brain_dev:8000'}/api/v1/webhooks/:path*`,
      },
      {
        source: '/api/v1/:path*',
        destination: `${process.env.INTERNAL_API_URL || 'http://visionarias_brain_dev:8000'}/api/v1/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
