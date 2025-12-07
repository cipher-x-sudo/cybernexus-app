/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Environment variables that will be available at runtime
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
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
