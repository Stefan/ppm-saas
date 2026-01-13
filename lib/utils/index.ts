/**
 * Utilities Barrel Export
 * Centralized exports for all utility functions
 */

export * from './design-system'
export * from './env'
export * from './error-handler'
export * from './web-workers'
export * from './code-splitting'

// Chrome-specific utilities - explicit exports to avoid conflicts
export * from './chrome-scroll-performance'
export {
  detectBrowser,
  isWebkitBasedBrowser,
  ChromeOptimizationManager,
  applyBrowserOptimizations,
  applyOptimizationsToElements,
  removeBrowserOptimizations,
  featureDetection,
  BROWSER_CLASSES,
  isChrome,
  isWebkit
} from './chrome-detection-optimization'
export * from './chrome-css-validation'
export * from './scroll-performance'

// Diagnostic and monitoring utilities
export * from '../diagnostics/diagnostic-collector'
export * from '../diagnostics/error-reporting'
export * from '../monitoring/logger'
export * from '../monitoring/performance-utils'