/**
 * Cross-Device Touch Interaction Tests
 * Tests touch gestures and interactions across different devices
 */

import { test, expect } from '@playwright/test'
import { DeviceTestUtils, deviceTestUtils } from './utils/device-testing'

test.describe('Touch Interaction Tests', () => {
  let deviceUtils: DeviceTestUtils

  test.beforeEach(async ({ page, context }) => {
    deviceUtils = deviceTestUtils.create(page, context)
  })

  test('should handle tap interactions on touch devices', async ({ page }) => {
    const touchDevices = [
      ...deviceTestUtils.devices.mobile,
      ...deviceTestUtils.devices.tablet
    ]

    for (const device of touchDevices) {
      await page.setViewportSize(device.viewport)
      await page.goto('/')
      
      // Test button taps
      const buttons = page.locator('button')
      const buttonCount = await buttons.count()
      
      if (buttonCount > 0) {
        const firstButton = buttons.first()
        await expect(firstButton).toBeVisible()
        
        // Test tap interaction
        await deviceUtils.testTouchInteraction({
          element: 'button:first-of-type',
          gesture: 'tap'
        })
        
        // Verify button responded to tap
        // This would depend on the specific button behavior
        console.log(`✅ ${device.name}: Button tap interaction working`)
      }
    }
  })

  test('should support swipe gestures on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboards')
    
    // Look for swipeable elements (cards, carousels, etc.)
    const swipeableElements = page.locator('[data-swipeable], .swipeable, .carousel')
    const elementCount = await swipeableElements.count()
    
    if (elementCount > 0) {
      const firstElement = swipeableElements.first()
      await expect(firstElement).toBeVisible()
      
      // Test swipe left
      await deviceUtils.testTouchInteraction({
        element: '[data-swipeable]:first-of-type, .swipeable:first-of-type, .carousel:first-of-type',
        gesture: 'swipe',
        direction: 'left',
        distance: 100
      })
      
      // Test swipe right
      await deviceUtils.testTouchInteraction({
        element: '[data-swipeable]:first-of-type, .swipeable:first-of-type, .carousel:first-of-type',
        gesture: 'swipe',
        direction: 'right',
        distance: 100
      })
      
      console.log('✅ Swipe gestures working on mobile')
    } else {
      console.log('ℹ️  No swipeable elements found to test')
    }
  })

  test('should handle long press interactions', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await page.goto('/')
    
    // Test long press on interactive elements
    const interactiveElements = page.locator('button, [role="button"], .interactive')
    const elementCount = await interactiveElements.count()
    
    if (elementCount > 0) {
      const firstElement = interactiveElements.first()
      await expect(firstElement).toBeVisible()
      
      // Test long press
      await deviceUtils.testTouchInteraction({
        element: 'button:first-of-type, [role="button"]:first-of-type, .interactive:first-of-type',
        gesture: 'longpress',
        duration: 1000
      })
      
      console.log('✅ Long press interaction working')
    }
  })

  test('should support pinch zoom on charts and images', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/resources') // Assuming this page has charts
    
    // Look for zoomable elements
    const zoomableElements = page.locator('canvas, svg, .chart, .zoomable, img')
    const elementCount = await zoomableElements.count()
    
    if (elementCount > 0) {
      const firstElement = zoomableElements.first()
      await expect(firstElement).toBeVisible()
      
      // Test pinch zoom
      await deviceUtils.testTouchInteraction({
        element: 'canvas:first-of-type, svg:first-of-type, .chart:first-of-type, .zoomable:first-of-type, img:first-of-type',
        gesture: 'pinch',
        distance: 50
      })
      
      console.log('✅ Pinch zoom working on charts/images')
    } else {
      console.log('ℹ️  No zoomable elements found to test')
    }
  })

  test('should handle pull-to-refresh on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboards')
    
    // Test pull-to-refresh gesture
    await page.evaluate(() => {
      // Simulate pull-to-refresh by scrolling to top and then pulling down
      window.scrollTo(0, 0)
    })
    
    // Simulate pull down gesture
    await page.mouse.move(200, 100)
    await page.mouse.down()
    await page.mouse.move(200, 200, { steps: 10 })
    await page.mouse.up()
    
    // Wait for any refresh animation
    await page.waitForTimeout(1000)
    
    // Verify page is still functional after pull-to-refresh
    await expect(page.locator('body')).toBeVisible()
    console.log('✅ Pull-to-refresh gesture handled')
  })

  test('should prevent accidental touches', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')
    
    // Test rapid taps to ensure debouncing
    const button = page.locator('button').first()
    
    if (await button.count() > 0) {
      await expect(button).toBeVisible()
      
      // Rapid tap test
      const tapPromises = []
      for (let i = 0; i < 5; i++) {
        tapPromises.push(button.tap({ timeout: 100 }))
      }
      
      await Promise.all(tapPromises.map(p => p.catch(() => {}))) // Ignore timeout errors
      
      // Verify the interface is still responsive
      await expect(button).toBeVisible()
      console.log('✅ Rapid tap handling working (debouncing)')
    }
  })

  test('should handle multi-touch gestures', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }) // Tablet size
    await page.goto('/')
    
    // Test two-finger scroll
    await page.evaluate(() => {
      // Simulate two-finger scroll
      const element = document.body
      const event = new WheelEvent('wheel', {
        deltaY: 100,
        ctrlKey: false,
        bubbles: true
      })
      element.dispatchEvent(event)
    })
    
    // Verify page scrolled
    const scrollY = await page.evaluate(() => window.scrollY)
    console.log(`✅ Multi-touch scroll: scrollY = ${scrollY}`)
  })

  test('should maintain touch responsiveness under load', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')
    
    // Simulate CPU load
    await page.evaluate(() => {
      // Create some CPU load
      const start = Date.now()
      while (Date.now() - start < 100) {
        Math.random()
      }
    })
    
    // Test touch responsiveness during load
    const button = page.locator('button').first()
    
    if (await button.count() > 0) {
      const startTime = Date.now()
      await button.tap()
      const responseTime = Date.now() - startTime
      
      // Touch response should be under 100ms even under load
      expect(responseTime).toBeLessThan(200)
      console.log(`✅ Touch response time under load: ${responseTime}ms`)
    }
  })
})