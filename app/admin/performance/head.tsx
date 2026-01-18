/**
 * Custom Head for Admin Performance Page
 * Adds resource hints and preloading for critical resources
 */

export default function Head() {
  return (
    <>
      {/* Preload critical API endpoints */}
      <link 
        rel="preload" 
        href="/api/admin/performance/stats" 
        as="fetch" 
        crossOrigin="anonymous"
      />
      <link 
        rel="preload" 
        href="/api/admin/performance/health" 
        as="fetch" 
        crossOrigin="anonymous"
      />
      <link 
        rel="preload" 
        href="/api/admin/cache/stats" 
        as="fetch" 
        crossOrigin="anonymous"
      />
      
      {/* Preload chart library chunk (lazy loaded) */}
      <link 
        rel="prefetch" 
        href="/_next/static/chunks/charts-vendor.js" 
        as="script"
      />
    </>
  )
}
