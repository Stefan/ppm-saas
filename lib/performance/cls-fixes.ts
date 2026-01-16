/**
 * CLS (Cumulative Layout Shift) Performance Fixes
 * 
 * This module provides utilities and configurations to prevent layout shifts
 * and improve Core Web Vitals scores.
 */

/**
 * Reserve space for fixed positioned elements to prevent layout shifts
 * Apply this to the body or main container
 */
export const reserveFixedElementSpace = () => {
  if (typeof document === 'undefined') return

  // Add CSS to reserve space for fixed elements
  const style = document.createElement('style')
  style.textContent = `
    /* Reserve space for help chat toggle button */
    body {
      padding-top: env(safe-area-inset-top);
      padding-right: env(safe-area-inset-right);
    }
    
    /* Prevent layout shifts from fixed elements */
    .fixed-element-container {
      contain: layout style paint;
      will-change: auto;
    }
    
    /* Ensure images always have aspect ratio */
    img:not([width]):not([height]) {
      aspect-ratio: attr(width) / attr(height);
    }
    
    /* Prevent font loading shifts */
    body {
      font-display: optional;
    }
    
    /* Stabilize dynamic content areas */
    .dynamic-content-area {
      min-height: 200px;
      contain: layout;
    }
    
    /* Prevent animation-induced shifts */
    .animate-pulse,
    .animate-bounce,
    .animate-spin {
      will-change: transform, opacity;
      transform: translateZ(0);
    }
  `
  
  if (!document.head.querySelector('#cls-fixes')) {
    style.id = 'cls-fixes'
    document.head.appendChild(style)
  }
}

/**
 * Configuration for image loading to prevent CLS
 */
export const imageLoadingConfig = {
  // Always use these attributes on images
  loading: 'lazy' as const,
  decoding: 'async' as const,
  
  // Placeholder for images without dimensions
  placeholder: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E',
  
  // Default aspect ratios for common image types
  aspectRatios: {
    thumbnail: '1 / 1',
    card: '16 / 9',
    banner: '21 / 9',
    portrait: '3 / 4',
    square: '1 / 1'
  }
}

/**
 * Utility to calculate aspect ratio from dimensions
 */
export const calculateAspectRatio = (width: number, height: number): string => {
  const gcd = (a: number, b: number): number => b === 0 ? a : gcd(b, a % b)
  const divisor = gcd(width, height)
  return `${width / divisor} / ${height / divisor}`
}

/**
 * Wrapper component props for CLS-safe containers
 */
export interface CLSSafeContainerProps {
  minHeight?: string | number
  aspectRatio?: string
  className?: string
  children: React.ReactNode
}

/**
 * Get optimal skeleton dimensions based on content type
 */
export const getSkeletonDimensions = (variant: string) => {
  const dimensions = {
    stat: { height: '120px', aspectRatio: undefined },
    project: { height: '180px', aspectRatio: undefined },
    resource: { height: '200px', aspectRatio: undefined },
    risk: { height: '160px', aspectRatio: undefined },
    chart: { height: '320px', aspectRatio: '16 / 9' },
    table: { height: '400px', aspectRatio: undefined },
    card: { height: '240px', aspectRatio: '16 / 9' }
  }
  
  return dimensions[variant as keyof typeof dimensions] || dimensions.stat
}

/**
 * Initialize CLS prevention on app load
 */
export const initializeCLSPrevention = () => {
  if (typeof window === 'undefined') return

  // Reserve space for fixed elements
  reserveFixedElementSpace()
  
  // Add observer for dynamic content
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) { // Element node
          const element = node as HTMLElement
          
          // Check for images without dimensions
          if (element.tagName === 'IMG') {
            const img = element as HTMLImageElement
            if (!img.width && !img.height && !img.style.aspectRatio) {
              console.warn('Image without dimensions detected:', img.src)
              // Set a default aspect ratio to prevent shift
              img.style.aspectRatio = '16 / 9'
            }
          }
          
          // Check for fixed positioned elements
          const computedStyle = window.getComputedStyle(element)
          if (computedStyle.position === 'fixed' || computedStyle.position === 'absolute') {
            element.style.willChange = 'transform'
            element.style.transform = 'translateZ(0)'
          }
        }
      })
    })
  })
  
  // Observe the entire document
  observer.observe(document.body, {
    childList: true,
    subtree: true
  })
  
  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    observer.disconnect()
  })
  
  return observer
}

/**
 * Utility to preload critical images
 */
export const preloadCriticalImages = (imageUrls: string[]) => {
  if (typeof document === 'undefined') return

  imageUrls.forEach(url => {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.as = 'image'
    link.href = url
    document.head.appendChild(link)
  })
}

/**
 * Utility to add font-display: optional to web fonts
 */
export const optimizeFontLoading = () => {
  if (typeof document === 'undefined') return

  const style = document.createElement('style')
  style.textContent = `
    @font-face {
      font-display: optional;
    }
  `
  document.head.appendChild(style)
}
