/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Environment variables that will be available at build time
  // NOTE: NEXT_PUBLIC_* variables are embedded at build time
  // Make sure to set NEXT_PUBLIC_API_URL in Railway before building
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
  // Inject API URL into window for runtime access (fallback)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.plugins.push(
        new (require('webpack')).DefinePlugin({
          'process.env.NEXT_PUBLIC_API_URL': JSON.stringify(
            process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
          ),
        })
      );
    }
    return config;
  },
  // Only use rewrites in development
  async rewrites() {
    // In production, the frontend should call the backend directly via NEXT_PUBLIC_API_URL
    if (process.env.NODE_ENV === 'production') {
      return [];
    }
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
