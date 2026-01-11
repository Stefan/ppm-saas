import '@testing-library/jest-dom'

// Import custom testing utilities
import { toMeetTouchTargetRequirements, toHaveResponsiveLayout } from './__tests__/utils/responsive-testing'
import { toBeAccessible } from './__tests__/utils/accessibility-testing'

// Extend Jest matchers
expect.extend({
  toMeetTouchTargetRequirements,
  toHaveResponsiveLayout,
  toBeAccessible
})

// Add polyfills for Node.js environment
if (typeof TextEncoder === 'undefined') {
  global.TextEncoder = require('util').TextEncoder
}

if (typeof TextDecoder === 'undefined') {
  global.TextDecoder = require('util').TextDecoder
}

if (typeof ReadableStream === 'undefined') {
  global.ReadableStream = require('stream/web').ReadableStream
}

// Mock IndexedDB for testing environment
if (typeof indexedDB === 'undefined') {
  global.indexedDB = {
    open: jest.fn(),
    deleteDatabase: jest.fn(),
  }
}

// Mock PerformanceObserver and performance APIs for diagnostic tests
if (typeof PerformanceObserver === 'undefined') {
  global.PerformanceObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    disconnect: jest.fn()
  }))
}

if (typeof performance === 'undefined') {
  global.performance = {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
    measure: jest.fn(),
    getEntriesByName: jest.fn(() => []),
    getEntriesByType: jest.fn(() => []),
    memory: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000
    }
  }
}

// Mock localStorage
if (typeof localStorage === 'undefined') {
  global.localStorage = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn()
  }
}

// Mock screen object
if (typeof screen === 'undefined') {
  global.screen = {
    width: 1920,
    height: 1080,
    colorDepth: 24
  }
}

// Mock Intl for timezone
if (typeof Intl === 'undefined') {
  global.Intl = {
    DateTimeFormat: jest.fn(() => ({
      resolvedOptions: () => ({ timeZone: 'UTC' })
    }))
  }
}

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    }
  },
  useSearchParams() {
    return new URLSearchParams()
  },
  usePathname() {
    return ''
  },
}))

// Mock Supabase
jest.mock('./app/providers/SupabaseAuthProvider', () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    clearSession: jest.fn(),
  }),
}))

// Mock service worker for PWA tests
Object.defineProperty(window, 'navigator', {
  value: {
    serviceWorker: {
      register: jest.fn(() => Promise.resolve()),
      ready: Promise.resolve({
        unregister: jest.fn(() => Promise.resolve()),
      }),
    },
    userAgent: 'Mozilla/5.0 (Test Browser) TestKit/1.0',
    platform: 'Test Platform',
    language: 'en-US',
    cookieEnabled: true,
    onLine: true
  },
  writable: true,
})