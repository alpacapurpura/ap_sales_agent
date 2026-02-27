/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  devIndicators: {
    buildActivity: true,
    buildActivityPosition: 'bottom-left',
  },
  // Whitelist local domains for development to prevent "Cross origin request detected" errors
  allowedDevOrigins: ["salesagent.local", "api.salesagent.local", "admin.salesagent.local", "laptopchris.alpacapurpura.lat"],
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'salesagent.alpacapurpura.lat',
      },
      {
        protocol: 'https',
        hostname: 'apisalesagent.alpacapurpura.lat', // Production API
      },
      {
        protocol: 'https',
        hostname: 'laptopchris.alpacapurpura.lat',
      },
      {
        protocol: 'https',
        hostname: 'laptopchris-api.alpacapurpura.lat', // Development API Tunnel
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
      allowedOrigins: ['salesagent.local', 'localhost:3000', 'laptopchris.alpacapurpura.lat', 'salesagent.alpacapurpura.lat', 'clerk.alpacapurpura.lat']
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
