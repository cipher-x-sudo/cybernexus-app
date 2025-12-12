/** @type {import('next').NextConfig} */
// Log environment variable during build (will show in Railway logs)
console.log('========================================');
console.log('[Railway Build] Environment Variables:');
console.log(`NEXT_PUBLIC_API_URL = ${process.env.NEXT_PUBLIC_API_URL || '(not set - will use localhost fallback)'}`);
console.log(`NODE_ENV = ${process.env.NODE_ENV || 'development'}`);
console.log('========================================');

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
