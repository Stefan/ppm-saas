import type { NextConfig } from "next";
import withPWA from 'next-pwa';

const nextConfig: NextConfig = {
  // Performance optimizations
  compress: true,
  poweredByHeader: false,
  
  // Production optimizations
  productionBrowserSourceMaps: false,
  
  // Bundle optimization
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts', '@headlessui/react'],
    optimizeCss: true,
    webVitalsAttribution: ['CLS', 'LCP'],
  },
  
  // Turbopack configuration (empty to silence warnings)
  turbopack: {},
  
  // Compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
    styledComponents: false, // Disable if not using styled-components
  },
  
  // Bundle analyzer and optimization
  webpack: (config, { dev, isServer }) => {
    // Only optimize in production
    if (!dev && !isServer) {
      // Minimize bundle size
      config.optimization.usedExports = true
      config.optimization.sideEffects = false
    }
    
    return config
  },
  
  // Environment variables validation
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // TypeScript configuration
  typescript: {
    ignoreBuildErrors: true, // Skip type checking in production build
    tsconfigPath: './tsconfig.prod.json',
  },

  // Image optimization
  images: {
    formats: ['image/webp', 'image/avif'],
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

  // Redirects for API calls
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://orka-ppm.onrender.com'}/:path*`,
      },
    ];
  },
};

// PWA Configuration - Simplified for faster builds
const pwaConfig = withPWA({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
  skipWaiting: true,
  // Minimal runtime caching for faster builds
  runtimeCaching: []
});

export default pwaConfig(nextConfig as any);
