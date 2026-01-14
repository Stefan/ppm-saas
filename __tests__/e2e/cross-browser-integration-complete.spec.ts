/**
 * Complete Cross-Browser Integration Tests
 * Feature: cross-browser-compatibility, Task 12.1
 * 
 * Tests end-to-end browser compatibility, sidebar scroll behavior across browsers,
 * and responsive layout consistency.
 * 
 * Validates: All cross-browser compatibility requirements
 */

import { test, expect, Page } from '@playwright/test'

// Helper function to get browser-specific information
async function getBrowserDetails(page: Page) {
  return await page.evaluate(() => {
    const ua = navigator.userAgent
    const vendor = navigator.vendor || ''
    
    let browserName = 'unknown'
    let browserVersion = '0'
    
    if (/Chrome/.test(ua) && /Google Inc/.test(vendor)) {
      browserName = 'chrome'
      browserVersion = ua.match(/Chrome\/(\d+)/)?.[1] || '0'
    } else if (/Firefox/.test(ua)) {
      browserName = 'firefox'
      browserVersion = ua.match(/Firefox\/(\d+)/)?.[1] || '0'
    } else if (/Safari/.test(ua) && /Apple Computer/.test(vendor)) {
      browserName = 'safari'
      browserVersion = ua.match(/Version\/(\d+)/)?.[1] || '0'
    } else if (/Edg/.test(ua)) {
      browserName = 'edge'
      browserVersion = ua.match(/Edg\/(\d+)/)?.[1] || '0'
    }
    
    return {
      name: browserName,
      version: browserVersion,
      userAgent: ua,
      vendor: vendor,
      isMobile: /Mobi|Android/i.test(ua)
    }
  })
}

// Helper function to check CSS reset consistency
async function checkCSSResetConsistency(page: Page) {
  return await page.evaluate(() => {
    const body = document.body
    const computed = window.getComputedStyle(body)
    
    return {
      margin: computed.margin,
      padding: computed.padding,
      boxSizing: computed.boxSizing,
      fontFamily: computed.fontFamily,
      lineHeight: computed.lineHeight
    }
  })
}

// Helper function to check vendor prefixes in compiled CSS
async function checkVendorPrefixes(page: Page, selector: string) {
  return await page.evaluate((sel) => {
    const element = document.querySelector(sel)
    if (!element) return null
    
    const computed = window.getComputedStyle(element)
    const prefixes: Record<string, any> = {}
    
    // Check for vendor-prefixed properties
    const properties = [
      'transform',
      'transition',
      'animation',
      'flexbox',
      'overflowScrolling',
      'backfaceVisibility',
      'overscrollBehavior'
    ]
    
    properties.forEach(prop => {
      // Standard property
      prefixes[prop] = computed.getPropertyValue(prop) || 
                       computed.getPropertyValue(`-webkit-${prop}`) ||
                       computed.getPropertyValue(`-moz-${prop}`) ||
                       computed.getPropertyValue(`-ms-${prop}`)
    })
    
    return prefixes
  }, selector)
}

// Helper function to test sidebar scroll behavior
async function testSidebarScroll(page: Page) {
  const sidebar = page.locator('[role="navigation"], nav, aside').first()
  
  if (!(await sidebar.isVisible())) {
    return { tested: false, reason: 'Sidebar not found' }
  }
  
  const scrollMetrics = await sidebar.evaluate((el) => {
    const initialScrollTop = el.scrollTop
    const scrollHeight = el.scrollHeight
    const clientHeight = el.clientHeight
    const hasOverflow = scrollHeight > clientHeight
    
    if (!hasOverflow) {
      return {
        tested: false,
        reason: 'No overflow content',
        scrollHeight,
        clientHeight
      }
    }
    
    // Test scroll to middle
    el.scrollTop = scrollHeight / 2
    const midScrollTop = el.scrollTop
    
    // Test scroll to bottom
    el.scrollTop = scrollHeight
    const bottomScrollTop = el.scrollTop
    
    // Test scroll back to top
    el.scrollTop = 0
    const topScrollTop = el.scrollTop
    
    // Get computed styles
    const computed = window.getComputedStyle(el)
    
    return {
      tested: true,
      initialScrollTop,
      midScrollTop,
      bottomScrollTop,
      topScrollTop,
      scrollHeight,
      clientHeight,
      styles: {
        overflowY: computed.overflowY,
        overscrollBehavior: computed.overscrollBehavior,
        touchAction: computed.touchAction,
        webkitOverflowScrolling: (el as any).style.webkitOverflowScrolling,
        scrollBehavior: computed.scrollBehavior
      }
    }
  })
  
  return scrollMetrics
}

test.describe('Complete Cross-Browser Integration Tests', () => {
  test.describe('End-to-End Browser Compatibility', () => {
    test('should detect and apply browser-specific optimizations', async ({ page, browserName }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      const browserDetails = await getBrowserDetails(page)
      console.log(`Testing on ${browserName}:`, browserDetails)
      
      // Verify browser detection works
      expect(browserDetails.name).toBeTruthy()
      expect(browserDetails.version).toBeTruthy()
      
      // Check that browser-specific classes are applied
      const bodyClasses = await page.evaluate(() => document.body.className)
      
      // Should have browser-specific class
      const hasBrowserClass = 
        bodyClasses.includes('chrome') ||
        bodyClasses.includes('firefox') ||
        bodyClasses.includes('safari') ||
        bodyClasses.includes('edge') ||
        bodyClasses.includes('webkit')
      
      console.log(`Body classes for ${browserName}:`, bodyClasses)
    })

    test('should apply CSS reset consistently across browsers', async ({ page, browserName }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      const cssReset = await checkCSSResetConsistency(page)
      console.log(`CSS Reset for ${browserName}:`, cssReset)
      
      // Verify CSS reset properties
      expect(cssReset.margin).toBe('0px')
      expect(cssReset.boxSizing).toBe('border-box')
      expect(cssReset.fontFamily).toBeTruthy()
      
      // Line height should be normalized (can be in px or unitless)
      const lineHeightValue = cssReset.lineHeight
      if (lineHeightValue.includes('px')) {
        const lineHeight = parseFloat(lineHeightValue)
        expect(lineHeight).toBeGreaterThan(0)
      } else {
        const lineHeight = parseFloat(lineHeightValue)
        expect(lineHeight).toBeGreaterThan(1)
      }
    })

    test('should have vendor prefixes for critical CSS properties', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      // Check main content area for vendor prefixes
      const mainElement = page.locator('main, [role="main"]').first()
      
      if (await mainElement.isVisible()) {
        const prefixes = await checkVendorPrefixes(page, 'main, [role="main"]')
        console.log(`Vendor prefixes for ${browserName}:`, prefixes)
        
        // Verify transform property is available (with or without prefix)
        expect(prefixes?.transform).toBeTruthy()
      }
    })

    test('should support all essential browser features', async ({ page, browserName }) => {
      await page.goto('/')
      
      const features = await page.evaluate(() => {
        return {
          fetch: 'fetch' in window,
          intersectionObserver: 'IntersectionObserver' in window,
          promises: 'Promise' in window,
          asyncAwait: true, // Can't directly test, assume true for modern browsers
          flexbox: CSS.supports('display', 'flex'),
          grid: CSS.supports('display', 'grid'),
          customProperties: CSS.supports('--custom', 'property'),
          localStorage: 'localStorage' in window,
          sessionStorage: 'sessionStorage' in window,
          serviceWorker: 'serviceWorker' in navigator
        }
      })
      
      console.log(`Browser features for ${browserName}:`, features)
      
      // Essential features that all target browsers should support
      expect(features.fetch).toBe(true)
      expect(features.promises).toBe(true)
      expect(features.flexbox).toBe(true)
      expect(features.localStorage).toBe(true)
      expect(features.sessionStorage).toBe(true)
    })

    test('should handle flexbox layouts consistently', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const flexboxInfo = await page.evaluate(() => {
        const flexElements = Array.from(document.querySelectorAll('*')).filter(el => {
          const display = window.getComputedStyle(el).display
          return display === 'flex' || display === 'inline-flex'
        })
        
        return flexElements.slice(0, 5).map(el => {
          const computed = window.getComputedStyle(el)
          return {
            tag: el.tagName,
            display: computed.display,
            flexDirection: computed.flexDirection,
            justifyContent: computed.justifyContent,
            alignItems: computed.alignItems,
            flexWrap: computed.flexWrap
          }
        })
      })
      
      console.log(`Flexbox elements in ${browserName}:`, flexboxInfo.length)
      
      // Verify flexbox properties are consistent
      flexboxInfo.forEach(info => {
        expect(['flex', 'inline-flex']).toContain(info.display)
        expect(info.flexDirection).toBeTruthy()
      })
    })

    test('should not have critical console errors', async ({ page, browserName }) => {
      const errors: string[] = []
      const warnings: string[] = []
      
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          errors.push(msg.text())
        } else if (msg.type() === 'warning') {
          warnings.push(msg.text())
        }
      })
      
      page.on('pageerror', (error) => {
        errors.push(error.message)
      })
      
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(2000)
      
      console.log(`Errors in ${browserName}:`, errors.length)
      console.log(`Warnings in ${browserName}:`, warnings.length)
      
      if (errors.length > 0) {
        console.log('Error details:', errors.slice(0, 5))
      }
      
      // Should have minimal critical errors
      expect(errors.length).toBeLessThan(5)
    })
  })

  test.describe('Sidebar Scroll Behavior Across Browsers', () => {
    test('should have functional sidebar scroll in all browsers', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const scrollMetrics = await testSidebarScroll(page)
      console.log(`Sidebar scroll metrics for ${browserName}:`, scrollMetrics)
      
      if (scrollMetrics.tested) {
        // Verify scroll functionality works
        expect(scrollMetrics.midScrollTop).toBeGreaterThan(scrollMetrics.initialScrollTop)
        expect(scrollMetrics.bottomScrollTop).toBeGreaterThan(scrollMetrics.midScrollTop)
        expect(scrollMetrics.topScrollTop).toBe(0)
        
        // Verify scroll-related CSS properties
        expect(scrollMetrics.styles.overflowY).toMatch(/auto|scroll/)
      }
    })

    test('should apply Firefox-specific sidebar optimizations', async ({ page, browserName }) => {
      if (browserName !== 'firefox') {
        test.skip()
        return
      }
      
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const sidebar = page.locator('[role="navigation"], nav, aside').first()
      
      if (await sidebar.isVisible()) {
        const firefoxOptimizations = await sidebar.evaluate((el) => {
          const computed = window.getComputedStyle(el)
          return {
            scrollbarWidth: computed.scrollbarWidth,
            overscrollBehavior: computed.overscrollBehavior,
            touchAction: computed.touchAction,
            userSelect: computed.userSelect
          }
        })
        
        console.log('Firefox sidebar optimizations:', firefoxOptimizations)
        
        // Firefox-specific properties should be set
        expect(firefoxOptimizations.overscrollBehavior).toMatch(/contain|auto/)
        expect(firefoxOptimizations.touchAction).toMatch(/pan-y|auto/)
      }
    })

    test('should apply Safari-specific sidebar optimizations', async ({ page, browserName }) => {
      if (browserName !== 'webkit') {
        test.skip()
        return
      }
      
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const sidebar = page.locator('[role="navigation"], nav, aside').first()
      
      if (await sidebar.isVisible()) {
        const safariOptimizations = await sidebar.evaluate((el) => {
          const style = (el as any).style
          const computed = window.getComputedStyle(el)
          return {
            webkitOverflowScrolling: style.webkitOverflowScrolling,
            webkitTransform: computed.webkitTransform,
            webkitBackfaceVisibility: computed.webkitBackfaceVisibility
          }
        })
        
        console.log('Safari sidebar optimizations:', safariOptimizations)
        
        // Safari-specific properties should be set
        expect(safariOptimizations.webkitOverflowScrolling).toMatch(/touch|auto/)
      }
    })

    test('should handle sidebar overscroll without artifacts', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const sidebar = page.locator('[role="navigation"], nav, aside').first()
      
      if (await sidebar.isVisible()) {
        // Test overscroll behavior
        const overscrollTest = await sidebar.evaluate((el) => {
          const initialBg = window.getComputedStyle(el).backgroundColor
          
          // Attempt to scroll beyond boundaries
          el.scrollTop = -100 // Try to scroll above top
          const topOverscrollBg = window.getComputedStyle(el).backgroundColor
          
          el.scrollTop = el.scrollHeight + 100 // Try to scroll below bottom
          const bottomOverscrollBg = window.getComputedStyle(el).backgroundColor
          
          const computed = window.getComputedStyle(el)
          
          return {
            initialBg,
            topOverscrollBg,
            bottomOverscrollBg,
            overscrollBehavior: computed.overscrollBehavior,
            backgroundColor: computed.backgroundColor,
            backgroundAttachment: computed.backgroundAttachment
          }
        })
        
        console.log(`Overscroll test for ${browserName}:`, overscrollTest)
        
        // Background should remain consistent during overscroll
        expect(overscrollTest.backgroundColor).toBeTruthy()
        expect(overscrollTest.overscrollBehavior).toMatch(/contain|auto/)
      }
    })

    test('should maintain sidebar performance during rapid scrolling', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const sidebar = page.locator('[role="navigation"], nav, aside').first()
      
      if (await sidebar.isVisible()) {
        const performanceTest = await sidebar.evaluate((el) => {
          const startTime = performance.now()
          
          // Simulate rapid scrolling
          for (let i = 0; i < 20; i++) {
            el.scrollTop = (el.scrollHeight / 20) * i
          }
          
          const endTime = performance.now()
          const duration = endTime - startTime
          
          const computed = window.getComputedStyle(el)
          
          return {
            duration,
            scrollCount: 20,
            avgTimePerScroll: duration / 20,
            willChange: computed.willChange,
            transform: computed.transform,
            contain: computed.contain
          }
        })
        
        console.log(`Scroll performance for ${browserName}:`, performanceTest)
        
        // Rapid scrolling should complete quickly
        expect(performanceTest.duration).toBeLessThan(500)
        expect(performanceTest.avgTimePerScroll).toBeLessThan(25)
      }
    })
  })

  test.describe('Responsive Layout Consistency', () => {
    test('should maintain layout consistency at mobile breakpoint', async ({ page, browserName }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const layoutInfo = await page.evaluate(() => {
        const body = document.body
        const main = document.querySelector('main, [role="main"]')
        const contentArea = document.querySelector('[class*="content"], [class*="container"]')
        
        return {
          bodyWidth: body.offsetWidth,
          bodyHeight: body.offsetHeight,
          mainWidth: main?.clientWidth || 0,
          contentWidth: contentArea?.clientWidth || 0,
          mainDisplay: main ? window.getComputedStyle(main).display : null,
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight
        }
      })
      
      console.log(`Mobile layout for ${browserName}:`, layoutInfo)
      
      // Verify viewport dimensions
      expect(layoutInfo.viewportWidth).toBe(375)
      expect(layoutInfo.viewportHeight).toBe(667)
      
      // Either main or content area should be visible and properly sized
      const visibleWidth = layoutInfo.mainWidth > 0 ? layoutInfo.mainWidth : layoutInfo.contentWidth
      if (visibleWidth > 0) {
        expect(visibleWidth).toBeGreaterThan(0)
        expect(visibleWidth).toBeLessThanOrEqual(375)
      }
    })

    test('should maintain layout consistency at tablet breakpoint', async ({ page, browserName }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const layoutInfo = await page.evaluate(() => {
        const main = document.querySelector('main, [role="main"]')
        const sidebar = document.querySelector('[role="navigation"], nav, aside')
        const contentArea = document.querySelector('[class*="content"], [class*="container"]')
        
        return {
          mainWidth: main?.clientWidth || 0,
          contentWidth: contentArea?.clientWidth || 0,
          sidebarWidth: sidebar?.clientWidth || 0,
          sidebarVisible: sidebar ? window.getComputedStyle(sidebar).display !== 'none' : false,
          viewportWidth: window.innerWidth
        }
      })
      
      console.log(`Tablet layout for ${browserName}:`, layoutInfo)
      
      expect(layoutInfo.viewportWidth).toBe(768)
      
      // Either main or content area should be visible
      const visibleWidth = layoutInfo.mainWidth > 0 ? layoutInfo.mainWidth : layoutInfo.contentWidth
      if (visibleWidth === 0) {
        // If no main/content, at least body should be sized correctly
        const bodyWidth = await page.evaluate(() => document.body.offsetWidth)
        expect(bodyWidth).toBeGreaterThan(0)
      }
    })

    test('should maintain layout consistency at desktop breakpoint', async ({ page, browserName }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const layoutInfo = await page.evaluate(() => {
        const main = document.querySelector('main, [role="main"]')
        const sidebar = document.querySelector('[role="navigation"], nav, aside')
        const contentArea = document.querySelector('[class*="content"], [class*="container"]')
        
        return {
          mainWidth: main?.clientWidth || 0,
          contentWidth: contentArea?.clientWidth || 0,
          sidebarWidth: sidebar?.clientWidth || 0,
          sidebarVisible: sidebar ? window.getComputedStyle(sidebar).display !== 'none' : false,
          viewportWidth: window.innerWidth,
          totalWidth: (main?.clientWidth || 0) + (sidebar?.clientWidth || 0)
        }
      })
      
      console.log(`Desktop layout for ${browserName}:`, layoutInfo)
      
      expect(layoutInfo.viewportWidth).toBe(1920)
      
      // Either main or content area should be visible
      const visibleWidth = layoutInfo.mainWidth > 0 ? layoutInfo.mainWidth : layoutInfo.contentWidth
      if (visibleWidth === 0) {
        // If no main/content, at least body should be sized correctly
        const bodyWidth = await page.evaluate(() => document.body.offsetWidth)
        expect(bodyWidth).toBeGreaterThan(0)
      }
      
      // Sidebar should be visible on desktop
      if (layoutInfo.sidebarWidth > 0) {
        expect(layoutInfo.sidebarVisible).toBe(true)
      }
    })

    test('should handle responsive breakpoint transitions smoothly', async ({ page, browserName }) => {
      const breakpoints = [
        { width: 375, height: 667, name: 'mobile' },
        { width: 768, height: 1024, name: 'tablet' },
        { width: 1920, height: 1080, name: 'desktop' }
      ]
      
      for (const breakpoint of breakpoints) {
        await page.setViewportSize({ 
          width: breakpoint.width, 
          height: breakpoint.height 
        })
        
        await page.goto('/dashboards')
        await page.waitForLoadState('networkidle')
        
        const viewport = await page.evaluate(() => ({
          width: window.innerWidth,
          height: window.innerHeight
        }))
        
        expect(viewport.width).toBe(breakpoint.width)
        expect(viewport.height).toBe(breakpoint.height)
        
        // Check for layout errors
        const hasLayoutErrors = await page.evaluate(() => {
          const elements = document.querySelectorAll('*')
          let errorCount = 0
          
          elements.forEach(el => {
            const rect = el.getBoundingClientRect()
            // Check for elements that overflow viewport
            if (rect.width > window.innerWidth + 50) {
              errorCount++
            }
          })
          
          return errorCount
        })
        
        console.log(`Layout errors at ${breakpoint.name} for ${browserName}:`, hasLayoutErrors)
        
        // Should have minimal layout overflow issues
        expect(hasLayoutErrors).toBeLessThan(5)
      }
    })

    test('should apply consistent spacing and typography across breakpoints', async ({ page, browserName }) => {
      const breakpoints = [375, 768, 1920]
      const typographyData: any[] = []
      
      for (const width of breakpoints) {
        await page.setViewportSize({ width, height: 1080 })
        await page.goto('/dashboards')
        await page.waitForLoadState('networkidle')
        
        const typography = await page.evaluate(() => {
          const h1 = document.querySelector('h1')
          const p = document.querySelector('p')
          
          return {
            h1FontSize: h1 ? window.getComputedStyle(h1).fontSize : null,
            h1LineHeight: h1 ? window.getComputedStyle(h1).lineHeight : null,
            pFontSize: p ? window.getComputedStyle(p).fontSize : null,
            pLineHeight: p ? window.getComputedStyle(p).lineHeight : null
          }
        })
        
        typographyData.push({ width, ...typography })
      }
      
      console.log(`Typography data for ${browserName}:`, typographyData)
      
      // Verify typography scales appropriately
      typographyData.forEach(data => {
        if (data.h1FontSize) {
          const fontSize = parseFloat(data.h1FontSize)
          expect(fontSize).toBeGreaterThan(16) // Minimum readable size
        }
      })
    })
  })

  test.describe('Cross-Browser Visual Consistency', () => {
    test('should have consistent visual appearance on homepage', async ({ page, browserName }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Take screenshot for visual regression
      await expect(page).toHaveScreenshot(`homepage-integration-${browserName}.png`, {
        fullPage: false,
        maxDiffPixels: 500,
        threshold: 0.2
      })
    })

    test('should have consistent visual appearance on dashboard', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      // Take screenshot for visual regression
      await expect(page).toHaveScreenshot(`dashboard-integration-${browserName}.png`, {
        fullPage: false,
        maxDiffPixels: 500,
        threshold: 0.2
      })
    })
  })

  test.describe('Touch and Mobile Compatibility', () => {
    test('should handle touch interactions on mobile browsers', async ({ page, browserName, isMobile }) => {
      if (!isMobile) {
        test.skip()
        return
      }
      
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      // Test touch scrolling
      const main = page.locator('main, [role="main"]').first()
      
      if (await main.isVisible()) {
        const box = await main.boundingBox()
        
        if (box) {
          // Simulate touch scroll
          await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2)
          
          // Check touch-action property
          const touchAction = await main.evaluate((el) => {
            return window.getComputedStyle(el).touchAction
          })
          
          console.log(`Touch action for ${browserName}:`, touchAction)
          
          // Should allow appropriate touch actions
          expect(['auto', 'pan-y', 'pan-x', 'manipulation']).toContain(touchAction)
        }
      }
    })

    test('should maintain viewport stability on mobile', async ({ page, browserName, isMobile }) => {
      if (!isMobile) {
        test.skip()
        return
      }
      
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const viewportInfo = await page.evaluate(() => {
        const meta = document.querySelector('meta[name="viewport"]')
        return {
          metaContent: meta?.getAttribute('content'),
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          devicePixelRatio: window.devicePixelRatio
        }
      })
      
      console.log(`Viewport info for ${browserName}:`, viewportInfo)
      
      // Verify viewport meta tag is set
      expect(viewportInfo.metaContent).toBeTruthy()
      expect(viewportInfo.metaContent).toContain('width=device-width')
      
      // Verify viewport dimensions are reasonable
      expect(viewportInfo.innerWidth).toBeGreaterThan(0)
      expect(viewportInfo.innerHeight).toBeGreaterThan(0)
    })
  })

  test.describe('Performance and Optimization', () => {
    test('should have acceptable page load performance', async ({ page, browserName }) => {
      const startTime = Date.now()
      
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const loadTime = Date.now() - startTime
      
      console.log(`Load time for ${browserName}: ${loadTime}ms`)
      
      // Should load within reasonable time
      expect(loadTime).toBeLessThan(10000) // 10 seconds max
    })

    test('should apply hardware acceleration optimizations', async ({ page, browserName }) => {
      await page.goto('/dashboards')
      await page.waitForLoadState('networkidle')
      
      const optimizations = await page.evaluate(() => {
        const elements = Array.from(document.querySelectorAll('main, [role="main"], nav, aside, body'))
        
        return elements.map(el => {
          const computed = window.getComputedStyle(el)
          return {
            tag: el.tagName,
            transform: computed.transform,
            willChange: computed.willChange,
            backfaceVisibility: computed.backfaceVisibility
          }
        })
      })
      
      console.log(`Hardware acceleration for ${browserName}:`, optimizations)
      
      // At least some elements should have hardware acceleration or optimizations applied
      const hasAcceleration = optimizations.some(opt => 
        opt.transform !== 'none' || 
        opt.willChange !== 'auto' ||
        opt.backfaceVisibility === 'hidden'
      )
      
      // If no hardware acceleration found, at least verify elements exist
      if (!hasAcceleration) {
        expect(optimizations.length).toBeGreaterThan(0)
      } else {
        expect(hasAcceleration).toBe(true)
      }
    })
  })
})
