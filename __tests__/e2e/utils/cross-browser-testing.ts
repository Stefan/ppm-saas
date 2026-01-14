/**
 * Cross-Browser Testing Utilities
 * Provides helpers for browser detection, performance monitoring, and visual regression testing
 */

import { Page, BrowserContext } from '@playwright/test'

export interface BrowserInfo {
  name: string
  version: string
  engine: string
  isMobile: boolean
  viewport: { width: number; height: number }
}

export interface PerformanceMetrics {
  loadTime: number
  domContentLoaded: number
  firstPaint: number
  firstContentfulPaint: number
  largestContentfulPaint: number
  timeToInteractive: number
  totalBlockingTime: number
  cumulativeLayoutShift: number
}

export interface ScrollPerformanceMetrics {
  averageFPS: number
  minFPS: number
  maxFPS: number
  scrollDuration: number
  frameDrops: number
}

/**
 * Get browser information from the page context
 */
export async function getBrowserInfo(page: Page): Promise<BrowserInfo> {
  return await page.evaluate(() => {
    const ua = navigator.userAgent
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight
    }

    let name = 'unknown'
    let engine = 'unknown'
    let version = '0'

    if (ua.includes('Chrome') && !ua.includes('Edg')) {
      name = 'chrome'
      engine = 'blink'
      version = ua.match(/Chrome\/(\d+)/)?.[1] || '0'
    } else if (ua.includes('Firefox')) {
      name = 'firefox'
      engine = 'gecko'
      version = ua.match(/Firefox\/(\d+)/)?.[1] || '0'
    } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
      name = 'safari'
      engine = 'webkit'
      version = ua.match(/Version\/(\d+)/)?.[1] || '0'
    } else if (ua.includes('Edg')) {
      name = 'edge'
      engine = 'blink'
      version = ua.match(/Edg\/(\d+)/)?.[1] || '0'
    }

    const isMobile = /Mobi|Android/i.test(ua)

    return { name, version, engine, isMobile, viewport }
  })
}

/**
 * Collect performance metrics from the page
 */
export async function collectPerformanceMetrics(page: Page): Promise<PerformanceMetrics> {
  return await page.evaluate(() => {
    const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
    const paintEntries = performance.getEntriesByType('paint')
    
    const firstPaint = paintEntries.find(e => e.name === 'first-paint')?.startTime || 0
    const firstContentfulPaint = paintEntries.find(e => e.name === 'first-contentful-paint')?.startTime || 0

    // Get LCP if available
    let largestContentfulPaint = 0
    if ('PerformanceObserver' in window) {
      try {
        const lcpEntries = performance.getEntriesByType('largest-contentful-paint')
        if (lcpEntries.length > 0) {
          largestContentfulPaint = lcpEntries[lcpEntries.length - 1].startTime
        }
      } catch (e) {
        // LCP not available
      }
    }

    return {
      loadTime: perfData.loadEventEnd - perfData.fetchStart,
      domContentLoaded: perfData.domContentLoadedEventEnd - perfData.fetchStart,
      firstPaint,
      firstContentfulPaint,
      largestContentfulPaint,
      timeToInteractive: perfData.domInteractive - perfData.fetchStart,
      totalBlockingTime: 0, // Would need more complex calculation
      cumulativeLayoutShift: 0 // Would need PerformanceObserver
    }
  })
}

/**
 * Measure scroll performance
 */
export async function measureScrollPerformance(
  page: Page,
  selector: string
): Promise<ScrollPerformanceMetrics> {
  return await page.evaluate((sel) => {
    const element = document.querySelector(sel)
    if (!element) {
      throw new Error(`Element not found: ${sel}`)
    }

    const frameTimes: number[] = []
    let lastFrameTime = performance.now()
    let animationFrameId: number

    return new Promise<ScrollPerformanceMetrics>((resolve) => {
      const measureFrame = () => {
        const currentTime = performance.now()
        const frameTime = currentTime - lastFrameTime
        frameTimes.push(frameTime)
        lastFrameTime = currentTime

        if (frameTimes.length < 60) {
          animationFrameId = requestAnimationFrame(measureFrame)
        } else {
          cancelAnimationFrame(animationFrameId)
          
          // Calculate metrics
          const fps = frameTimes.map(t => 1000 / t)
          const averageFPS = fps.reduce((a, b) => a + b, 0) / fps.length
          const minFPS = Math.min(...fps)
          const maxFPS = Math.max(...fps)
          const frameDrops = fps.filter(f => f < 30).length
          const scrollDuration = frameTimes.reduce((a, b) => a + b, 0)

          resolve({
            averageFPS,
            minFPS,
            maxFPS,
            scrollDuration,
            frameDrops
          })
        }
      }

      // Start scroll animation
      const scrollHeight = element.scrollHeight - element.clientHeight
      element.scrollTop = 0
      
      animationFrameId = requestAnimationFrame(measureFrame)
      
      // Perform smooth scroll
      element.scrollTo({
        top: scrollHeight,
        behavior: 'smooth'
      })
    })
  }, selector)
}

/**
 * Check if browser supports specific features
 */
export async function checkBrowserFeatures(page: Page): Promise<Record<string, boolean>> {
  return await page.evaluate(() => {
    return {
      intersectionObserver: 'IntersectionObserver' in window,
      resizeObserver: 'ResizeObserver' in window,
      mutationObserver: 'MutationObserver' in window,
      fetch: 'fetch' in window,
      promises: 'Promise' in window,
      asyncAwait: true, // If code runs, async/await is supported
      flexbox: CSS.supports('display', 'flex'),
      grid: CSS.supports('display', 'grid'),
      customProperties: CSS.supports('--custom', 'property'),
      webGL: (() => {
        try {
          const canvas = document.createElement('canvas')
          return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
        } catch (e) {
          return false
        }
      })(),
      serviceWorker: 'serviceWorker' in navigator,
      webWorker: 'Worker' in window,
      localStorage: (() => {
        try {
          localStorage.setItem('test', 'test')
          localStorage.removeItem('test')
          return true
        } catch (e) {
          return false
        }
      })(),
      sessionStorage: (() => {
        try {
          sessionStorage.setItem('test', 'test')
          sessionStorage.removeItem('test')
          return true
        } catch (e) {
          return false
        }
      })()
    }
  })
}

/**
 * Apply browser-specific CSS classes for testing
 */
export async function applyBrowserSpecificClasses(page: Page): Promise<void> {
  await page.evaluate(() => {
    const ua = navigator.userAgent
    const html = document.documentElement

    if (ua.includes('Chrome') && !ua.includes('Edg')) {
      html.classList.add('browser-chrome')
    } else if (ua.includes('Firefox')) {
      html.classList.add('browser-firefox')
    } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
      html.classList.add('browser-safari')
    } else if (ua.includes('Edg')) {
      html.classList.add('browser-edge')
    }

    if (/Mobi|Android/i.test(ua)) {
      html.classList.add('device-mobile')
    } else {
      html.classList.add('device-desktop')
    }
  })
}

/**
 * Wait for animations to complete
 */
export async function waitForAnimations(page: Page, selector?: string): Promise<void> {
  await page.evaluate((sel) => {
    return new Promise<void>((resolve) => {
      const elements = sel 
        ? Array.from(document.querySelectorAll(sel))
        : [document.body]

      if (elements.length === 0) {
        resolve()
        return
      }

      let animationCount = 0
      
      elements.forEach(element => {
        const animations = element.getAnimations()
        animationCount += animations.length

        animations.forEach(animation => {
          animation.finished.then(() => {
            animationCount--
            if (animationCount === 0) {
              resolve()
            }
          })
        })
      })

      if (animationCount === 0) {
        resolve()
      }

      // Timeout after 5 seconds
      setTimeout(() => resolve(), 5000)
    })
  }, selector)
}

/**
 * Compare visual differences between screenshots
 */
export interface VisualDifference {
  pixelDifference: number
  percentageDifference: number
  hasDifferences: boolean
}

/**
 * Get computed styles for an element
 */
export async function getComputedStyles(
  page: Page,
  selector: string,
  properties: string[]
): Promise<Record<string, string>> {
  return await page.evaluate(
    ({ sel, props }) => {
      const element = document.querySelector(sel)
      if (!element) {
        throw new Error(`Element not found: ${sel}`)
      }

      const computed = window.getComputedStyle(element)
      const styles: Record<string, string> = {}

      props.forEach(prop => {
        styles[prop] = computed.getPropertyValue(prop)
      })

      return styles
    },
    { sel: selector, props: properties }
  )
}

/**
 * Check for console errors
 */
export async function collectConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = []
  
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text())
    }
  })

  page.on('pageerror', (error) => {
    errors.push(error.message)
  })

  return errors
}

/**
 * Test touch interactions
 */
export async function testTouchInteraction(
  page: Page,
  selector: string
): Promise<boolean> {
  try {
    const element = page.locator(selector)
    const box = await element.boundingBox()
    
    if (!box) {
      return false
    }

    // Simulate touch tap
    await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2)
    
    // Wait for any response
    await page.waitForTimeout(100)
    
    return true
  } catch (error) {
    return false
  }
}

/**
 * Generate cross-browser test report
 */
export interface CrossBrowserTestReport {
  browser: BrowserInfo
  performance: PerformanceMetrics
  features: Record<string, boolean>
  errors: string[]
  timestamp: Date
}

export async function generateTestReport(page: Page): Promise<CrossBrowserTestReport> {
  const browser = await getBrowserInfo(page)
  const performance = await collectPerformanceMetrics(page)
  const features = await checkBrowserFeatures(page)
  const errors = await collectConsoleErrors(page)

  return {
    browser,
    performance,
    features,
    errors,
    timestamp: new Date()
  }
}
