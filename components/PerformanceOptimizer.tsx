'use client'

import { useEffect } from 'react'

/**
 * Performance optimization component
 * Handles various performance improvements
 */
export default function PerformanceOptimizer() {
  useEffect(() => {
    // Remove console logs in production
    if (process.env.NODE_ENV === 'production') {
      console.log = () => {}
      console.warn = () => {}
      console.info = () => {}
    }

    // Optimize images loading
    const images = document.querySelectorAll('img[loading="lazy"]')
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement
            if (img.dataset.src) {
              img.src = img.dataset.src
              img.removeAttribute('data-src')
              imageObserver.unobserve(img)
            }
          }
        })
      })
      
      images.forEach((img) => imageObserver.observe(img))
    }

    // Preload critical resources
    const preloadCriticalResources = () => {
      const criticalResources = [
        '/api/optimized/dashboard/quick-stats',
        '/api/projects'
      ]
      
      criticalResources.forEach((resource) => {
        const link = document.createElement('link')
        link.rel = 'prefetch'
        link.href = resource
        document.head.appendChild(link)
      })
    }

    // Delay non-critical resource preloading
    setTimeout(preloadCriticalResources, 2000)

    // Cleanup function
    return () => {
      // Cleanup observers if needed
    }
  }, [])

  return null // This component doesn't render anything
}