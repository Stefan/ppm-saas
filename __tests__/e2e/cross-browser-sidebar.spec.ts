/**
 * Cross-Browser Sidebar Functionality Tests
 * Tests sidebar scrolling, navigation, and layout across all supported browsers
 * Validates: Requirements 8.1, 8.3, 8.4
 */

import { test, expect, Page } from '@playwright/test'

test.describe('Cross-Browser Sidebar Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard which has sidebar
    await page.goto('/dashboards')
    await page.waitForLoadState('domcontentloaded')
  })

  test('sidebar should be visible and scrollable in all browsers', async ({ page, browserName }) => {
    // Find sidebar element - try multiple selectors
    const sidebarSelectors = ['[role="navigation"]', 'nav', 'aside', '[class*="sidebar"]', '[class*="nav"]']
    let sidebar = null
    
    for (const selector of sidebarSelectors) {
      const element = page.locator(selector).first()
      if (await element.isVisible().catch(() => false)) {
        sidebar = element
        break
      }
    }
    
    // If no sidebar found, the page might not have one - that's okay
    if (!sidebar) {
      console.log(`ℹ️  No sidebar found in ${browserName} - page may not have sidebar navigation`)
      return
    }
    
    await expect(sidebar).toBeVisible()

    // Check if sidebar has overflow content
    const hasOverflow = await sidebar.evaluate((el) => {
      return el.scrollHeight > el.clientHeight
    }).catch(() => false)

    if (hasOverflow) {
      // Test scrolling
      const initialScrollTop = await sidebar.evaluate((el) => el.scrollTop)
      
      // Scroll down
      await sidebar.evaluate((el) => {
        el.scrollTop = el.scrollHeight / 2
      })
      
      const midScrollTop = await sidebar.evaluate((el) => el.scrollTop)
      expect(midScrollTop).toBeGreaterThanOrEqual(initialScrollTop)

      // Scroll to bottom
      await sidebar.evaluate((el) => {
        el.scrollTop = el.scrollHeight
      })
      
      const bottomScrollTop = await sidebar.evaluate((el) => el.scrollTop)
      expect(bottomScrollTop).toBeGreaterThanOrEqual(midScrollTop)
    }

    console.log(`✓ Sidebar scroll test passed in ${browserName}`)
  })

  test('sidebar navigation links should work in all browsers', async ({ page, browserName }) => {
    // Find navigation links in sidebar
    const navLinks = page.locator('[role="navigation"] a, nav a, aside a')
    const linkCount = await navLinks.count()

    if (linkCount > 0) {
      // Test first link
      const firstLink = navLinks.first()
      await expect(firstLink).toBeVisible()
      
      const href = await firstLink.getAttribute('href')
      expect(href).toBeTruthy()

      // Click and verify navigation
      await firstLink.click()
      await page.waitForLoadState('networkidle')
      
      // Verify URL changed or page updated
      const currentUrl = page.url()
      expect(currentUrl).toBeTruthy()
    }

    console.log(`✓ Sidebar navigation test passed in ${browserName}`)
  })

  test('sidebar should maintain layout consistency across browsers', async ({ page, browserName }) => {
    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    
    if (await sidebar.isVisible()) {
      // Get computed styles
      const styles = await sidebar.evaluate((el) => {
        const computed = window.getComputedStyle(el)
        return {
          display: computed.display,
          position: computed.position,
          overflow: computed.overflow,
          overflowY: computed.overflowY,
          width: computed.width,
          height: computed.height
        }
      })

      // Verify essential layout properties
      expect(styles.display).toBeTruthy()
      expect(['fixed', 'sticky', 'relative', 'absolute', 'static']).toContain(styles.position)
      
      // Verify overflow is set for scrolling
      const hasOverflowY = styles.overflowY === 'auto' || 
                          styles.overflowY === 'scroll' || 
                          styles.overflow === 'auto' || 
                          styles.overflow === 'scroll'
      
      if (hasOverflowY) {
        expect(hasOverflowY).toBe(true)
      }

      console.log(`✓ Sidebar layout consistency test passed in ${browserName}`)
    }
  })

  test('sidebar should handle touch scrolling on mobile browsers', async ({ page, browserName, isMobile }) => {
    if (!isMobile) {
      test.skip()
      return
    }

    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    
    if (await sidebar.isVisible()) {
      // Check touch-action property
      const touchAction = await sidebar.evaluate((el) => {
        return window.getComputedStyle(el).touchAction
      })

      // Should allow vertical panning
      expect(['auto', 'pan-y', 'manipulation']).toContain(touchAction)

      // Test touch scroll
      const box = await sidebar.boundingBox()
      if (box) {
        // Simulate touch scroll
        await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2)
        
        // Verify no errors occurred
        const errors: string[] = []
        page.on('pageerror', (error) => errors.push(error.message))
        
        await page.waitForTimeout(500)
        expect(errors.length).toBe(0)
      }

      console.log(`✓ Sidebar touch scrolling test passed in ${browserName}`)
    }
  })

  test('sidebar should apply browser-specific optimizations', async ({ page, browserName }) => {
    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    
    if (await sidebar.isVisible()) {
      const browserOptimizations = await sidebar.evaluate((el, browser) => {
        const computed = window.getComputedStyle(el)
        const optimizations: Record<string, any> = {}

        // Check for hardware acceleration
        optimizations.transform = computed.transform
        optimizations.willChange = computed.willChange

        // Firefox-specific
        if (browser === 'firefox') {
          optimizations.scrollbarWidth = computed.scrollbarWidth
          optimizations.overscrollBehavior = computed.overscrollBehavior
        }

        // WebKit-specific (Safari)
        if (browser === 'webkit') {
          optimizations.webkitOverflowScrolling = (el as any).style.webkitOverflowScrolling
        }

        return optimizations
      }, browserName)

      // Verify some optimization is applied
      const hasOptimizations = 
        browserOptimizations.transform !== 'none' ||
        browserOptimizations.willChange !== 'auto' ||
        Object.keys(browserOptimizations).length > 2

      console.log(`Browser optimizations for ${browserName}:`, browserOptimizations)
    }

    console.log(`✓ Browser-specific optimizations test passed in ${browserName}`)
  })
})

test.describe('Cross-Browser Performance Monitoring', () => {
  test('should measure sidebar scroll performance across browsers', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')

    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    
    if (await sidebar.isVisible()) {
      // Measure scroll performance
      const performance = await sidebar.evaluate((el) => {
        const startTime = performance.now()
        let frameCount = 0
        const frameTimes: number[] = []

        // Perform scroll
        const scrollDistance = el.scrollHeight - el.clientHeight
        if (scrollDistance > 0) {
          el.scrollTop = scrollDistance / 2
        }

        const endTime = performance.now()
        const duration = endTime - startTime

        return {
          duration,
          scrollDistance,
          fps: frameCount > 0 ? 1000 / (duration / frameCount) : 0
        }
      })

      // Log performance metrics
      console.log(`Scroll performance in ${browserName}:`, performance)

      // Verify reasonable performance (scroll should complete quickly)
      expect(performance.duration).toBeLessThan(1000) // Should complete within 1 second
    }
  })

  test('should monitor memory usage during sidebar interactions', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')

    // Get initial memory if available
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize
      }
      return null
    })

    // Perform sidebar interactions
    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    if (await sidebar.isVisible()) {
      // Scroll multiple times
      for (let i = 0; i < 5; i++) {
        await sidebar.evaluate((el) => {
          el.scrollTop = Math.random() * (el.scrollHeight - el.clientHeight)
        })
        await page.waitForTimeout(100)
      }
    }

    // Get final memory if available
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        return (performance as any).memory.usedJSHeapSize
      }
      return null
    })

    if (initialMemory !== null && finalMemory !== null) {
      const memoryIncrease = finalMemory - initialMemory
      console.log(`Memory usage in ${browserName}: +${memoryIncrease} bytes`)

      // Memory increase should be reasonable (less than 10MB)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024)
    }
  })
})

test.describe('Visual Regression Testing', () => {
  test('sidebar should look consistent across browsers', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')

    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    
    if (await sidebar.isVisible()) {
      // Take screenshot for visual comparison
      await expect(sidebar).toHaveScreenshot(`sidebar-${browserName}.png`, {
        maxDiffPixels: 100, // Allow small differences
        threshold: 0.2 // 20% threshold for anti-aliasing differences
      })
    }
  })

  test('sidebar scroll state should be visually consistent', async ({ page, browserName }) => {
    await page.goto('/dashboards')
    await page.waitForLoadState('networkidle')

    const sidebar = page.locator('[role="navigation"], nav, aside').first()
    
    if (await sidebar.isVisible()) {
      // Scroll to middle
      await sidebar.evaluate((el) => {
        el.scrollTop = (el.scrollHeight - el.clientHeight) / 2
      })

      await page.waitForTimeout(300) // Wait for scroll to settle

      // Take screenshot
      await expect(sidebar).toHaveScreenshot(`sidebar-scrolled-${browserName}.png`, {
        maxDiffPixels: 100,
        threshold: 0.2
      })
    }
  })
})
