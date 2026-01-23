/**
 * Visual Regression Test Suite
 * 
 * Tests for detecting visual changes across pages and viewports.
 * Requirements: 4.1, 4.2, 4.6
 * 
 * @visual
 */

import { test, expect, Page } from '@playwright/test';
import {
  VISUAL_REGRESSION_CONFIG,
  getViewport,
  getAllPageConfigs,
  type PageConfig,
  type ViewportConfig,
} from '@/lib/testing/visual-regression-config';

/**
 * Disable animations for consistent screenshots
 * Requirement 4.5: Disable animations
 */
async function disableAnimations(page: Page): Promise<void> {
  await page.addStyleTag({
    content: `
      *,
      *::before,
      *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `,
  });
}

/**
 * Wait for page to be ready for screenshot
 */
async function waitForPageReady(page: Page, pageConfig: PageConfig): Promise<void> {
  // Wait for network to be idle
  await page.waitForLoadState('networkidle');

  // Wait for specific selector if configured
  if (pageConfig.waitForSelector) {
    await page.waitForSelector(pageConfig.waitForSelector, {
      timeout: 10000,
      state: 'visible',
    });
  }

  // Additional wait for any dynamic content
  await page.waitForTimeout(500);
}

/**
 * Apply masks to dynamic elements
 */
async function applyMasks(page: Page, pageConfig: PageConfig): Promise<void> {
  if (!pageConfig.maskSelectors || pageConfig.maskSelectors.length === 0) {
    return;
  }

  for (const selector of pageConfig.maskSelectors) {
    const elements = await page.locator(selector).all();
    for (const element of elements) {
      await element.evaluate((el) => {
        (el as HTMLElement).style.visibility = 'hidden';
      });
    }
  }
}

test.describe('Visual Regression Tests', { tag: '@visual' }, () => {
  test.beforeEach(async ({ page }) => {
    // Disable animations for all tests
    await disableAnimations(page);
  });

  // Requirement 4.1: Capture baseline screenshots for all main pages
  // Requirement 4.6: Multiple viewport sizes
  for (const pageConfig of getAllPageConfigs()) {
    for (const viewportName of pageConfig.viewports) {
      test(`${pageConfig.name} page - ${viewportName} viewport`, async ({ page }) => {
        const viewport = getViewport(viewportName);

        // Set viewport size
        await page.setViewportSize({
          width: viewport.width,
          height: viewport.height,
        });

        // Navigate to page
        await page.goto(pageConfig.path);

        // Wait for page to be ready
        await waitForPageReady(page, pageConfig);

        // Apply masks to dynamic elements
        await applyMasks(page, pageConfig);

        // Requirement 4.2: Compare screenshots with threshold
        await expect(page).toHaveScreenshot(
          `${pageConfig.name}-${viewportName}.png`,
          {
            threshold: VISUAL_REGRESSION_CONFIG.threshold,
            maxDiffPixels: VISUAL_REGRESSION_CONFIG.maxDiffPixels,
            fullPage: true,
          }
        );
      });
    }
  }
});

test.describe('Visual Regression - Critical Components', { tag: '@visual' }, () => {
  test.beforeEach(async ({ page }) => {
    await disableAnimations(page);
  });

  test('dashboard KPI cards - desktop', async ({ page }) => {
    const viewport = getViewport('desktop');
    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    });

    await page.goto('/dashboards');
    await page.waitForSelector('[data-testid="dashboard-kpi-section"]', {
      state: 'visible',
    });

    const kpiSection = page.locator('[data-testid="dashboard-kpi-section"]');
    await expect(kpiSection).toHaveScreenshot('dashboard-kpi-cards.png', {
      threshold: VISUAL_REGRESSION_CONFIG.threshold,
      maxDiffPixels: VISUAL_REGRESSION_CONFIG.maxDiffPixels,
    });
  });

  test('variance section - desktop', async ({ page }) => {
    const viewport = getViewport('desktop');
    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    });

    await page.goto('/dashboards');
    await page.waitForSelector('[data-testid="dashboard-variance-section"]', {
      state: 'visible',
    });

    const varianceSection = page.locator('[data-testid="dashboard-variance-section"]');
    await expect(varianceSection).toHaveScreenshot('dashboard-variance-section.png', {
      threshold: VISUAL_REGRESSION_CONFIG.threshold,
      maxDiffPixels: VISUAL_REGRESSION_CONFIG.maxDiffPixels,
    });
  });

  test('navigation bar - mobile', async ({ page }) => {
    const viewport = getViewport('mobile');
    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    });

    await page.goto('/dashboards');
    await page.waitForSelector('[data-testid="mobile-nav"]', {
      state: 'visible',
    });

    const mobileNav = page.locator('[data-testid="mobile-nav"]');
    await expect(mobileNav).toHaveScreenshot('mobile-nav.png', {
      threshold: VISUAL_REGRESSION_CONFIG.threshold,
      maxDiffPixels: VISUAL_REGRESSION_CONFIG.maxDiffPixels,
    });
  });
});

test.describe('Visual Regression - Responsive Breakpoints', { tag: '@visual' }, () => {
  test.beforeEach(async ({ page }) => {
    await disableAnimations(page);
  });

  const breakpoints = [
    { name: 'mobile-small', width: 320, height: 568 },
    { name: 'mobile-medium', width: 375, height: 667 },
    { name: 'mobile-large', width: 414, height: 896 },
    { name: 'tablet-portrait', width: 768, height: 1024 },
    { name: 'tablet-landscape', width: 1024, height: 768 },
    { name: 'desktop-small', width: 1366, height: 768 },
    { name: 'desktop-large', width: 1920, height: 1080 },
  ];

  for (const breakpoint of breakpoints) {
    test(`dashboard responsive layout - ${breakpoint.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: breakpoint.width,
        height: breakpoint.height,
      });

      await page.goto('/dashboards');
      await page.waitForSelector('[data-testid="dashboard-header"]', {
        state: 'visible',
      });
      await page.waitForLoadState('networkidle');

      await expect(page).toHaveScreenshot(
        `dashboard-responsive-${breakpoint.name}.png`,
        {
          threshold: VISUAL_REGRESSION_CONFIG.threshold,
          maxDiffPixels: VISUAL_REGRESSION_CONFIG.maxDiffPixels,
          fullPage: true,
        }
      );
    });
  }
});
