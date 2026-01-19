/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  devIndicators: {
    buildActivity: true,
    buildActivityPosition: 'bottom-left',
  },
  // Whitelist local domains for development to prevent "Cross origin request detected" errors
  allowedDevOrigins: ["salesagent.local", "api.salesagent.local", "admin.salesagent.local"],
  experimental: {
    serverActions: {
      allowedOrigins: ['salesagent.local', 'localhost:3000']
    }
  }
}

module.exports = nextConfig
