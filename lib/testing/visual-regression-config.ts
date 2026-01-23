/**
 * Visual Regression Testing Configuration
 * 
 * Defines pages, viewports, and thresholds for visual regression tests.
 * Requirements: 4.1, 4.5, 4.6
 */

export interface ViewportConfig {
  name: string;
  width: number;
  height: number;
}

export interface PageConfig {
  path: string;
  name: string;
  waitForSelector?: string;
  maskSelectors?: string[];
  viewports: string[];
}

export interface VisualRegressionConfig {
  pages: PageConfig[];
  threshold: number;
  maxDiffPixels: number;
  animations: 'disabled' | 'allow';
  viewports: Record<string, ViewportConfig>;
}

/**
 * Standard viewport configurations
 * Requirement 4.6: Multiple viewport sizes
 */
export const VIEWPORTS: Record<string, ViewportConfig> = {
  desktop: {
    name: 'desktop',
    width: 1920,
    height: 1080,
  },
  tablet: {
    name: 'tablet',
    width: 1024,
    height: 768,
  },
  mobile: {
    name: 'mobile',
    width: 375,
    height: 667,
  },
};

/**
 * Visual regression test configuration
 * Requirement 4.1: Baseline screenshots for all main pages
 * Requirement 4.5: Disable animations for consistent screenshots
 * Requirement 4.6: Multiple viewport sizes
 */
export const VISUAL_REGRESSION_CONFIG: VisualRegressionConfig = {
  pages: [
    {
      path: '/dashboards',
      name: 'dashboard',
      waitForSelector: '[data-testid="dashboard-header"]',
      maskSelectors: ['[data-testid="dashboard-refresh-button"]'],
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/projects',
      name: 'projects',
      waitForSelector: '[data-testid="projects-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/resources',
      name: 'resources',
      waitForSelector: '[data-testid="resources-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/financials',
      name: 'financials',
      waitForSelector: '[data-testid="financials-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/reports',
      name: 'reports',
      waitForSelector: '[data-testid="reports-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/audit',
      name: 'audit',
      waitForSelector: '[data-testid="audit-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/risks',
      name: 'risks',
      waitForSelector: '[data-testid="risks-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/scenarios',
      name: 'scenarios',
      waitForSelector: '[data-testid="scenarios-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/monte-carlo',
      name: 'monte-carlo',
      waitForSelector: '[data-testid="monte-carlo-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/admin',
      name: 'admin',
      waitForSelector: '[data-testid="admin-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/changes',
      name: 'changes',
      waitForSelector: '[data-testid="changes-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/feedback',
      name: 'feedback',
      waitForSelector: '[data-testid="feedback-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
    {
      path: '/import',
      name: 'import',
      waitForSelector: '[data-testid="import-header"]',
      viewports: ['desktop', 'tablet', 'mobile'],
    },
  ],
  threshold: 0.1, // 10% pixel difference threshold
  maxDiffPixels: 500, // Maximum allowed different pixels
  animations: 'disabled', // Requirement 4.5: Disable animations
  viewports: VIEWPORTS,
};

/**
 * Get viewport configuration by name
 */
export function getViewport(name: string): ViewportConfig {
  const viewport = VIEWPORTS[name];
  if (!viewport) {
    throw new Error(`Unknown viewport: ${name}`);
  }
  return viewport;
}

/**
 * Get page configuration by name
 */
export function getPageConfig(name: string): PageConfig | undefined {
  return VISUAL_REGRESSION_CONFIG.pages.find((page) => page.name === name);
}

/**
 * Get all page configurations
 */
export function getAllPageConfigs(): PageConfig[] {
  return VISUAL_REGRESSION_CONFIG.pages;
}
