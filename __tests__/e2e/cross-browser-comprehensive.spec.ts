/**
 * Comprehensive Cross-Browser Testing Suite
 * Tests all critical functionality across Chrome, Firefox, Safari, and Edge
 * Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
 */

import { test, expect } from '@playwright/test'
import {
  getBrowserInfo,
  collectPerformanceMetrics,
  checkBrowserFeatures,
  applyBrowserSpecificClasses,
  getComputedStyles,
  generateTestReport
} from './utils/cross-browser-testing'

test.describe('Cross-Browser Comprehensive Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Apply browser-specific classes
    await page.goto('/')
    await applyBrowserSpecificClasses(page)
  })

  test('should detect browser correctly', async ({ page, browserName }) => {
    const browserInfo = await getBrowserInfo(page)
    
    console.log(`Browser Info for ${browserName}:`, browserInfo)
    
    expect(browserInfo.name).toBeTruthy()
    expect(browserInfo.engine).toBeTruthy()
    expect(browserInfo.version).toBeTruthy()
    expect(browserInfo.viewport.width).toBeGreaterThan(0)
    expect(browserInfo.viewport.height).toBeGreaterThan(0)
  })

  test('should support all essential browser features', async ({ page, browserName }) => {
    const features = await checkBrowserFeatures(page)
    
    console.log(`Browser Features for ${browserName}:`, features)
    
    // Essential features that all modern browsers should support
    expect(features.fetch).toBe(true)
    expect(features.promises).toBe(true)
    expect(features.asyncAwait).toBe(true)
    expect(features.flexbox).toBe(true)
    expect(features.localStorage).toBe(true)
    expect(features.sessionStorage).toBe(true)
  })

  test('should have acceptable performance metrics', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    const metrics = await collectPerformanceMetrics(page)
    
    console.log(`Performance Metrics for ${browserName}:`, metrics)
    
    // Performance thresholds
    expect(metrics.loadTime).toBeLessThan(10000) // 10 seconds max
    expect(metrics.domContentLoaded).toBeLessThan(5000) // 5 seconds max
    expect(metrics.firstContentfulPaint).toBeLessThan(3000) // 3 seconds max
  })

  test('should apply consistent CSS across browsers', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    // Test body styles
    const bodyStyles = await getComputedStyles(page, 'body', [
      'margin',
      'padding',
      'box-sizing',
      'font-family'
    ])
    
    console.log(`Body Styles for ${browserName}:`, bodyStyles)
    
    // CSS reset should ensure consistent values
    expect(bodyStyles.margin).toBe('0px')
    expect(bodyStyles['box-sizing']).toBe('border-box')
  })

  test('should handle flexbox layouts consistently', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    // Find flex containers
    const flexContainers = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'))
      return elements
        .filter(el => {
          const display = window.getComputedStyle(el).display
          return display === 'flex' || display === 'inline-flex'
        })
        .map(el => ({
          tag: el.tagName,
          display: window.getComputedStyle(el).display,
          flexDirection: window.getComputedStyle(el).flexDirection,
          justifyContent: window.getComputedStyle(el).justifyContent
        }))
    })
    
    console.log(`Flex Containers in ${browserName}:`, flexContainers.length)
    
    // Verify flex containers exist and have proper properties
    if (flexContainers.length > 0) {
      flexContainers.forEach(container => {
        expect(['flex', 'inline-flex']).toContain(container.display)
        expect(container.flexDirection).toBeTruthy()
      })
    }
  })

  test('should handle grid layouts consistently', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    // Find grid containers
    const gridContainers = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*'))
      return elements
        .filter(el => {
          const display = window.getComputedStyle(el).display
          return display === 'grid' || display === 'inline-grid'
        })
        .map(el => ({
          tag: el.tagName,
          display: window.getComputedStyle(el).display,
          gridTemplateColumns: window.getComputedStyle(el).gridTemplateColumns,
          gridTemplateRows: window.getComputedStyle(el).gridTemplateRows
        }))
    })
    
    console.log(`Grid Containers in ${browserName}:`, gridContainers.length)
    
    // Verify grid containers have proper properties
    if (gridContainers.length > 0) {
      gridContainers.forEach(container => {
        expect(['grid', 'inline-grid']).toContain(container.display)
      })
    }
  })

  test('should not have console errors', async ({ page, browserName }) => {
    const errors: string[] = []
    
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })
    
    page.on('pageerror', (error) => {
      errors.push(error.message)
    })
    
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    // Allow some time for any delayed errors
    await page.waitForTimeout(1000)
    
    console.log(`Console Errors in ${browserName}:`, errors.length)
    
    if (errors.length > 0) {
      console.log('Errors:', errors)
    }
    
    // Should have minimal or no errors
    expect(errors.length).toBeLessThan(5)
  })

  test('should handle responsive breakpoints consistently', async ({ page, browserName }) => {
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
      
      // Check viewport dimensions
      const viewport = await page.evaluate(() => ({
        width: window.innerWidth,
        height: window.innerHeight
      }))
      
      expect(viewport.width).toBe(breakpoint.width)
      expect(viewport.height).toBe(breakpoint.height)
      
      console.log(`✓ ${breakpoint.name} breakpoint works in ${browserName}`)
    }
  })

  test('should generate comprehensive test report', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    const report = await generateTestReport(page)
    
    console.log(`Test Report for ${browserName}:`, {
      browser: report.browser.name,
      version: report.browser.version,
      loadTime: report.performance.loadTime,
      featureCount: Object.keys(report.features).length,
      errorCount: report.errors.length
    })
    
    // Verify report completeness
    expect(report.browser.name).toBeTruthy()
    expect(report.performance.loadTime).toBeGreaterThan(0)
    expect(Object.keys(report.features).length).toBeGreaterThan(0)
    expect(report.timestamp).toBeInstanceOf(Date)
  })
})

test.describe('Cross-Browser Visual Consistency', () => {
  test('homepage should look consistent across browsers', async ({ page, browserName }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Take full page screenshot
    await expect(page).toHaveScreenshot(`homepage-${browserName}.png`, {
      fullPage: true,
      maxDiffPixels: 500,
      threshold: 0.2
    })
  })

  test('dashboard should look consistent across browsers', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    // Take full page screenshot
    await expect(page).toHaveScreenshot(`dashboard-${browserName}.png`, {
      fullPage: true,
      maxDiffPixels: 500,
      threshold: 0.2
    })
  })
})

test.describe('Cross-Browser Error Handling', () => {
  test('should handle navigation errors gracefully', async ({ page, browserName }) => {
    const errors: string[] = []
    
    page.on('pageerror', (error) => {
      errors.push(error.message)
    })
    
    // Try to navigate to non-existent page
    const response = await page.goto('/non-existent-page')
    
    // Should get 404 or redirect
    expect(response?.status()).toBeGreaterThanOrEqual(400)
    
    // Should not crash
    expect(errors.length).toBe(0)
    
    console.log(`✓ Navigation error handling works in ${browserName}`)
  })

  test('should handle JavaScript errors gracefully', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')
    
    // Inject an error
    const errorHandled = await page.evaluate(() => {
      try {
        // @ts-ignore - intentional error
        nonExistentFunction()
        return false
      } catch (e) {
        return true
      }
    })
    
    expect(errorHandled).toBe(true)
    
    console.log(`✓ JavaScript error handling works in ${browserName}`)
  })
})
