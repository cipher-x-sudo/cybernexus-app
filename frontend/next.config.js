/** @type {import('next').NextConfig} */
// Log environment variable during build (will show in Railway logs)
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
console.log('\n');
console.log('═══════════════════════════════════════════════════════════');
console.log('🔧 Railway Build - Environment Variables');
console.log('═══════════════════════════════════════════════════════════');
if (apiUrl) {
  console.log('✅ NEXT_PUBLIC_API_URL: SET');
  console.log(`   Value: ${apiUrl}`);
} else {
  console.log('❌ NEXT_PUBLIC_API_URL: NOT SET');
  console.log('   ⚠️  Frontend will fail at runtime!');
  console.log('   📝 To fix: Set NEXT_PUBLIC_API_URL in Railway → Settings → Variables');
  console.log('   💡 Example: https://cybernexus-backend.up.railway.app/api/v1');
}
console.log(`📦 NODE_ENV: ${process.env.NODE_ENV || 'development'}`);
console.log('═══════════════════════════════════════════════════════════');
console.log('\n');

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
