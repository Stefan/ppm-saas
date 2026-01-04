import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Monorepo configuration - trace files from project root
  outputFileTracingRoot: process.cwd(),
  
  // Environment variables validation
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: false,
  },

  // Image optimization - using remotePatterns instead of deprecated domains
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'xceyrfvxooiplbmwavlb.supabase.co',
        port: '',
        pathname: '/**',
      },
    ],
    unoptimized: false,
  },

  // Output configuration for Vercel
  output: 'standalone',

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Redirects for API calls
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://backend-six-inky-90.vercel.app'}/:path*`,
      },
    ];
  },
};

export default nextConfig;
