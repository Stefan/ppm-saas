import { defineConfig, devices } from '@playwright/test'
import * as dotenv from 'dotenv'
import * as path from 'path'

// Load test environment variables
dotenv.config({ path: path.resolve(__dirname, '.env.test') })

// Auth file path for persistent authentication
const authFile = path.join(__dirname, 'playwright/.auth/user.json');

/**
 * Cross-Device Testing Configuration for Mobile-First UI Enhancements
 * Tests responsive behavior, touch interactions, and visual regression across devices
 */
export default defineConfig({
  testDir: './__tests__/e2e',
  testMatch: '**/*.spec.ts',
  
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : 4,
  
  // Reporter to use
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
  
  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Capture screenshot on failure
    screenshot: 'only-on-failure',
    
    // Record video on failure
    video: 'retain-on-failure',
    
    // Global test timeout
    actionTimeout: 10000,
    navigationTimeout: 30000
  },

  // Configure projects for major browsers and devices
  projects: [
    // Setup project for authentication
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
    },
    
    // Desktop browsers - depend on setup
    {
      name: 'chromium-desktop',
      dependencies: ['setup'],
      use: { 
        ...devices['Desktop Chrome'],
        storageState: authFile,
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'firefox-desktop',
      dependencies: ['setup'],
      use: { 
        ...devices['Desktop Firefox'],
        storageState: authFile,
        viewport: { width: 1920, height: 1080 }
      },
    },
    {
      name: 'webkit-desktop',
      dependencies: ['setup'],
      use: { 
        ...devices['Desktop Safari'],
        storageState: authFile,
        viewport: { width: 1920, height: 1080 }
      },
    },

    // Mobile devices - iOS
    {
      name: 'mobile-safari-iphone-12',
      dependencies: ['setup'],
      use: { ...devices['iPhone 12'], storageState: authFile },
    },
    {
      name: 'mobile-safari-iphone-12-pro',
      dependencies: ['setup'],
      use: { ...devices['iPhone 12 Pro'], storageState: authFile },
    },
    {
      name: 'mobile-safari-iphone-se',
      dependencies: ['setup'],
      use: { ...devices['iPhone SE'], storageState: authFile },
    },
    {
      name: 'mobile-safari-ipad',
      dependencies: ['setup'],
      use: { ...devices['iPad Pro'], storageState: authFile },
    },

    // Mobile devices - Android
    {
      name: 'mobile-chrome-pixel-5',
      dependencies: ['setup'],
      use: { ...devices['Pixel 5'], storageState: authFile },
    },
    {
      name: 'mobile-chrome-galaxy-s21',
      dependencies: ['setup'],
      use: { 
        ...devices['Galaxy S21'],
        storageState: authFile,
        viewport: { width: 384, height: 854 }
      },
    },

    // Tablets
    {
      name: 'tablet-chrome',
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: authFile,
        viewport: { width: 1024, height: 768 },
        isMobile: false,
        hasTouch: true
      },
    },
    {
      name: 'tablet-safari',
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Safari'],
        storageState: authFile,
        viewport: { width: 1024, height: 768 },
        isMobile: false,
        hasTouch: true
      },
    },

    // High DPI displays
    {
      name: 'high-dpi-desktop',
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: authFile,
        viewport: { width: 1920, height: 1080 },
        deviceScaleFactor: 2
      },
    },

    // Performance testing on slower devices
    {
      name: 'slow-device-simulation',
      dependencies: ['setup'],
      use: {
        ...devices['Desktop Chrome'],
        storageState: authFile,
        viewport: { width: 375, height: 667 },
        // Simulate slower device
        launchOptions: {
          args: [
            '--enable-features=NetworkService',
            '--disable-features=VizDisplayCompositor',
            '--disable-gpu',
            '--disable-dev-shm-usage'
          ]
        }
      },
    }
  ],

  // Global setup and teardown
  globalSetup: require.resolve('./__tests__/e2e/global-setup.ts'),
  globalTeardown: require.resolve('./__tests__/e2e/global-teardown.ts'),

  // Test timeout
  timeout: 30000,
  expect: {
    // Maximum time expect() should wait for the condition to be met
    timeout: 5000,
    
    // Visual comparison settings
    toHaveScreenshot: {
      threshold: 0.2,
      animations: 'disabled'
    }
  },

  // Web server configuration - always start server for tests
  webServer: {
    command: process.env.CI ? 'npm run build && npm run start' : 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 180000 // 3 minutes for build + start
  }
})