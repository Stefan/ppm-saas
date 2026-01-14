/**
 * React Hook for Progressive Enhancement
 * Provides feature detection and fallback strategies in React components
 */

import { useEffect, useState } from 'react'
import {
  detectFeatureSupport,
  getLayoutFallback,
  getAnimationFallback,
  initializeProgressiveEnhancement,
  type FeatureSupport
} from '@/lib/utils/progressive-enhancement'

/**
 * Hook to detect feature support
 */
export function useFeatureSupport(): FeatureSupport {
  const [features, setFeatures] = useState<FeatureSupport>(() => {
    // Initialize with default values for SSR
    if (typeof window === 'undefined') {
      return {
        css: {
          grid: true,
          flexbox: true,
          customProperties: true,
          transforms: true,
          transitions: true,
          animations: true,
          backdropFilter: true,
          clipPath: true,
          objectFit: true
        },
        js: {
          intersectionObserver: true,
          resizeObserver: true,
          mutationObserver: true,
          fetch: true,
          promises: true,
          asyncAwait: true,
          modules: true,
          webWorkers: true
        }
      }
    }
    return detectFeatureSupport()
  })

  useEffect(() => {
    // Update feature support on client side
    setFeatures(detectFeatureSupport())
  }, [])

  return features
}

/**
 * Hook to get layout fallback strategy
 */
export function useLayoutFallback(preferredLayout: 'grid' | 'flexbox'): 'grid' | 'flexbox' | 'float' {
  const [layout, setLayout] = useState<'grid' | 'flexbox' | 'float'>(preferredLayout)

  useEffect(() => {
    setLayout(getLayoutFallback(preferredLayout))
  }, [preferredLayout])

  return layout
}

/**
 * Hook to get animation fallback strategy
 */
export function useAnimationFallback(animationType: 'css' | 'js'): 'css' | 'js' | 'static' {
  const [fallback, setFallback] = useState<'css' | 'js' | 'static'>(animationType)

  useEffect(() => {
    setFallback(getAnimationFallback(animationType))
  }, [animationType])

  return fallback
}

/**
 * Hook to initialize progressive enhancement
 */
export function useProgressiveEnhancement(): void {
  useEffect(() => {
    initializeProgressiveEnhancement()
  }, [])
}

/**
 * Hook to check if a specific feature is supported
 */
export function useFeatureCheck(
  feature: keyof FeatureSupport['css'] | keyof FeatureSupport['js'],
  category: 'css' | 'js'
): boolean {
  const features = useFeatureSupport()
  
  if (category === 'css') {
    return features.css[feature as keyof FeatureSupport['css']]
  }
  
  return features.js[feature as keyof FeatureSupport['js']]
}

/**
 * Hook to get progressive enhancement classes
 */
export function useProgressiveClasses(): string {
  const features = useFeatureSupport()
  const [classes, setClasses] = useState<string>('')

  useEffect(() => {
    const classList: string[] = []

    // Add feature support classes
    if (features.css.grid) {
      classList.push('supports-grid')
    } else {
      classList.push('no-grid', 'fallback-flexbox')
    }

    if (features.css.flexbox) {
      classList.push('supports-flexbox')
    } else {
      classList.push('no-flexbox', 'fallback-float')
    }

    if (features.css.customProperties) {
      classList.push('supports-css-vars')
    } else {
      classList.push('no-css-vars')
    }

    if (features.css.transforms) {
      classList.push('supports-transforms')
    } else {
      classList.push('no-transforms')
    }

    if (features.css.animations) {
      classList.push('supports-animations')
    } else {
      classList.push('no-animations', 'static-fallback')
    }

    setClasses(classList.join(' '))
  }, [features])

  return classes
}
